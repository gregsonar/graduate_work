from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import UUID

import aiohttp
from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy import Boolean
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped
from starlette import status
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from auth.db.crud import AccessLogRepository, UserRepository, SocialAccountRepository
from auth.models.base_models import SocialProvider
from auth.models.user import User
from auth.models.user_account import UserSocialAccount
from auth.services.token_service import TokenService
from auth.services.user_service import logger
from typing_extensions import Optional

from auth.core.breaker import AsyncCircuitBreaker
from auth.core.base_service import circuit_protected
from auth.events.user_events import UserEventProducer, UserCreatedEvent
from auth.core.config import rabbit_config

# Создаем объект для работы с паролями
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService(UserRepository):
    def __init__(self, session: AsyncSession, redis):
        super().__init__(session)
        self.session = session
        self.redis = redis
        self.auth = TokenService(redis_client=self.redis, session=self.session)
        self.social_repository = SocialAccountRepository(session)
        self.circuit_breaker = AsyncCircuitBreaker(
            redis=redis,
            service_name="auth_service",
            failure_threshold=5,
            recovery_timeout=60
        )
        self.event_producer = UserEventProducer(rabbit_config)

    async def user_already_exists(self, username: str) -> Boolean:
        existing_user = await self.get_by_username(username)
        return existing_user is not None
        # raise HTTPException(status_code=400, detail="Username already exists")

    async def register_user(self, username: str,
                            password: str,
                            email: str| None,
                            is_superuser: bool = False) -> Dict[str, Any]:
        if await self.user_already_exists(username):
            raise HTTPException(status_code=400, detail="Username already exists")

        new_user_data = {
            "username": username,
            "password": password,
            "is_superuser": is_superuser,
            "email": email or self._generate_email()
        }

        new_user = await self.auth.user_repository.create(new_user_data)

        try:
            event = UserCreatedEvent(
                user_id=new_user.id,
                email=new_user.email
            )
            self.event_producer.publish_user_created(event)
        except Exception as e:
            logger.error(f"Failed to publish user created event: {e}")

        return {"id": str(new_user.id), "username": new_user.username}

    async def change_password(self, user_id: UUID, old_password: str, new_password: str):
        current_user = await self.get_by_id(user_id)

        if not current_user.check_password(old_password):
            raise HTTPException(status_code=401, detail="Password is incorrect")

        if not current_user:
            raise HTTPException(status_code=401, detail="User not found")

        new_user_data = {
            "password": new_password,
        }

        try:
            await self.update(current_user['id'], new_user_data)
        except Exception as e:
            raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error")

    @circuit_protected
    async def authenticate_user(self, username: str, password: str, user_creds: dict = Optional[dict]) -> Dict[str, Any]:
        user = await self.get_by_username(username)

        if not user or not user.check_password(password):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # if user_creds:
        #     await self.log_access(user.id, user_creds['ip'], user_creds['user_agent'])

        access_token, refresh_token = await self.auth.create_tokens_for_user(user.id)
        return {"access_token": access_token, "refresh_token": refresh_token}

    async def logout_user(self, access_token: str, refresh_token: str) -> bool:
        if await self.auth.is_token_blacklisted(refresh_token) or \
            await self.auth.is_token_blacklisted(access_token):
            return True

        try:
            await self.auth.blacklist_token(refresh_token)
            await self.auth.blacklist_token(access_token)
            return True
        except Exception as e:
            logger.error(str(e))
            raise e

    @circuit_protected
    async def refresh_token(self, token: str) -> Dict[str, Any]:
        try:
            # Проверка валидности токена происходит внутри auth.refresh_tokens
            new_access_token, new_refresh_token = await self.auth.refresh_tokens(token)
        except Exception as e:
            logger.error(str(e))
            raise e
        # Возвращаем в том же формате, что и authenticate_user
        return {"access_token": new_access_token, "refresh_token": new_refresh_token}

    async def log_access(self, user_id: Mapped[UUID], ip_address: str, user_agent: str) -> None:
        access_log_repo = AccessLogRepository(self.session)
        await access_log_repo.create_log(user_id=user_id, ip_address=ip_address, user_agent=user_agent)

    async def get_or_create_user(self, email: str, provider: str, username: str) -> User:
        user = None
        try:
            if not email and provider == SocialProvider.VK:
                user = await self.get_by_username(username)

            elif email:
                user = await self.get_by_email(email)

            if not user:
                # Создаем нового пользователя
                username = username or self._generate_username()
                user = await self.create(
                    {
                        "username": username,
                        "email": email
                    }
                )
                logger.info(f"Создан новый пользователь: {username}")
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при создании пользователя")
        return user

    @circuit_protected
    async def authenticate_social_user(
            self,
            provider: SocialProvider,
            social_id: str,
            social_data: Dict[str, Any],
            metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Аутентификация через социальную сеть с улучшенной обработкой ошибок
        и безопасностью
        """
        try:
            # Поиск существующего социального аккаунта
            social_account = await self.social_repository.get_by_provider_and_social_id(
                provider, social_id
            )

            if social_account:
                # Обновляем существующий аккаунт
                update_data = {
                    "access_token": social_data.get('access_token'),
                    "refresh_token": social_data.get('refresh_token'),
                    "token_expires_at": social_data.get('token_expires_at'),
                    "metadata": social_data.get('metadata', {}),
                    "avatar_url": social_data.get('avatar_url'),
                    "first_name": social_data.get('first_name'),
                    "last_name": social_data.get('last_name'),
                    "social_email": social_data.get('social_email'),
                }

                await self.social_repository.update(social_account.id, update_data)
                user = await self.get_by_id(social_account.user_id)
            else:
                # Создаем нового пользователя или находим существующего
                email = social_data.get('social_email')
                username = social_data.get('username') or self._generate_username()

                user = await self.get_user_by_social_identifiers(email, username, provider)
                if not user:
                    # Создаем нового пользователя
                    user = await self.create({
                        "username": username,
                        "email": email,
                        "avatar_url": social_data.get('avatar_url')
                    })

                # Создаем новый социальный аккаунт
                await self.social_repository.create({
                    "user_id": user.id,
                    "provider": provider,
                    "social_id": social_id,
                    "social_username": social_data.get('username'),
                    "social_email": email,
                    "first_name": social_data.get('first_name'),
                    "last_name": social_data.get('last_name'),
                    "avatar_url": social_data.get('avatar_url'),
                    "access_token": social_data.get('access_token'),
                    "refresh_token": social_data.get('refresh_token'),
                    "token_expires_at": social_data.get('token_expires_at'),
                    "metadata": social_data.get('metadata', {}),
                    "is_primary": True
                })

            # Если есть метаданные запроса, логируем доступ
            if metadata:
                await self.log_access(
                    user.id,
                    metadata.get('ip', 'unknown'),
                    metadata.get('user_agent', 'unknown')
                )

            # Создаем токены
            access_token, refresh_token = await self.auth.create_tokens_for_user(user.id)
            return {
                "access_token": access_token,
                "refresh_token": refresh_token
            }

        except Exception as e:
            logger.error(f"Social authentication error: {str(e)}")
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication failed: {str(e)}"
            )

    async def get_user_by_social_identifiers(
            self,
            email: Optional[str],
            username: str,
            provider: SocialProvider
    ) -> Optional[User]:
        """Поиск пользователя по email или username с учетом специфики провайдера"""
        user = None
        try:
            if email:
                user = await self.get_by_email(email)

            # Для VK проверяем также по username, так как email может отсутствовать
            if not user and provider == SocialProvider.VK:
                user = await self.get_by_username(username)

            return user
        except Exception as e:
            logger.error(f"Error finding user by social identifiers: {str(e)}")
            return None

    async def link_social_account(
            self,
            user_id: UUID,
            provider: SocialProvider,
            social_id: str,
            social_data: Dict[str, Any]
    ) -> UserSocialAccount:
        """Привязка социального аккаунта к существующему пользователю"""
        try:
            # Проверяем существование аккаунта
            existing_account = await self.social_repository.get_by_provider_and_social_id(
                provider, social_id
            )

            if existing_account:
                if existing_account.user_id == user_id:
                    # Обновляем существующий аккаунт
                    return await self.social_repository.update(
                        existing_account.id,
                        social_data
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="This social account is already linked to another user"
                    )

            # Создаем новый социальный аккаунт
            social_account = await self.social_repository.create({
                "user_id": user_id,
                "provider": provider,
                "social_id": social_id,
                **social_data
            })

            await self.session.commit()
            return social_account

        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error linking social account: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to link social account: {str(e)}"
            )

    async def unlink_social_account(
            self,
            user_id: UUID,
            provider: SocialProvider,
            social_id: str
    ) -> None:
        """Отвязка социального аккаунта с проверками безопасности"""
        try:
            # Получаем социальный аккаунт
            social_account = await self.social_repository.get_by_provider_and_social_id(
                provider, social_id
            )

            if not social_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Social account not found"
                )

            if social_account.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )

            # Проверяем, не является ли это единственным способом входа
            user = await self.get_by_id(user_id)
            if not user.password_hash and social_account.is_primary:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove primary authentication method without setting a password"
                )

            # Удаляем аккаунт
            await self.social_repository.delete(social_account.id)
            await self.session.commit()

        except HTTPException:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error unlinking social account: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to unlink social account: {str(e)}"
            )

    async def get_user_social_accounts(
            self,
            user_id: UUID,
            provider: Optional[SocialProvider] = None
    ) -> List[UserSocialAccount]:
        """Получение списка социальных аккаунтов пользователя"""
        try:
            return await self.social_repository.get_user_accounts(user_id, provider)
        except Exception as e:
            logger.error(f"Error getting user social accounts: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get social accounts"
            )

    @staticmethod
    def _generate_username():
        import random
        import string

        random_username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return random_username

    @staticmethod
    def _generate_email():
        import random
        import string

        random_email = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + "@auth.com"
        return random_email

