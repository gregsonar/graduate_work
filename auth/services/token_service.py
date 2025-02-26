import uuid
from datetime import UTC, datetime, timedelta
from logging import getLogger
from typing import Dict, Optional, Tuple
from uuid import UUID

import jwt
from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped

logger = getLogger(__name__)

from auth.core.base_service import circuit_protected
from auth.core.breaker import AsyncCircuitBreaker
from auth.core.config import TokenConfig
from auth.db.crud import UserRepository


class BlacklistError(Exception):
    pass


class TokenService:
    def __init__(self, redis_client: Redis, session: AsyncSession):
        self.redis_client = redis_client
        self.session = session
        self.config = TokenConfig()
        self.user_repository = UserRepository(session)
        self.circuit_breaker = AsyncCircuitBreaker(
            redis=redis_client,
            service_name="token_service",
            failure_threshold=3,
            recovery_timeout=30,
        )

    async def create_access_token(
        self, user_id: UUID, username: str, is_superuser: bool, roles: list[str]
    ) -> Optional[str]:
        """
        Create JWT access token for user authentication.

        Args:
            user_id (UUID): The unique identifier of the user
            username (str): The username of the user
            is_superuser (bool): Flag indicating if user has superuser privileges
            roles (list[str]): List of role names assigned to the user

        Returns:
            Optional[str]: JWT token string if successful, None if failed
        """
        try:
            logger.debug(f"Creating access token for user: {username} (ID: {user_id})")

            now = datetime.now(UTC)
            expires_delta = timedelta(minutes=self.config.access_token_expire_minutes)
            expire = now + expires_delta

            # Generate unique token ID
            token_id = str(uuid.uuid4())

            payload = {
                "user_id": str(user_id),
                "username": username,
                "is_superuser": is_superuser,
                "roles": roles,
                "exp": expire.timestamp(),
                "iat": now.timestamp(),
                "jti": token_id,  # Добавляем JTI
                "token_type": "access",
            }

            token = jwt.encode(
                payload, self.config.secret_key, algorithm=self.config.algorithm
            )

            logger.info(
                f"Access token created successfully for user {username} "
                f"(ID: {user_id}), JTI: {token_id}, expires at {expire.isoformat()}"
            )

            return token

        except Exception as e:
            error_msg = (
                f"Failed to create access token for user {username} (ID: {user_id})"
            )
            logger.error(f"{error_msg}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
            )

    async def create_refresh_token(self, user_id: UUID) -> Optional[str]:
        """
        Create JWT refresh token for user session renewal.

        Args:
            user_id (UUID): The unique identifier of the user

        Returns:
            Optional[str]: JWT refresh token if successful, None if failed
        """
        try:
            logger.debug(f"Creating refresh token for user ID: {user_id}")

            now = datetime.now(UTC)
            expires_delta = timedelta(days=self.config.refresh_token_expire_days)
            expire = now + expires_delta

            # Generate unique token ID
            token_id = str(uuid.uuid4())

            payload = {
                "user_id": str(user_id),
                "exp": expire.timestamp(),
                "iat": now.timestamp(),
                "jti": token_id,
                "token_type": "refresh",
            }

            token = jwt.encode(
                payload, self.config.secret_key, algorithm=self.config.algorithm
            )

            logger.info(
                f"Refresh token created successfully for user ID: {user_id}, "
                f"JTI: {token_id}, expires at {expire.isoformat()}"
            )

            return token

        except Exception as e:
            error_msg = f"Failed to create refresh token for user ID {user_id}"
            logger.error(f"{error_msg}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
            )

    @circuit_protected
    async def validate_token(
        self, token: str, verify_exp: bool = True
    ) -> Optional[Dict]:
        """
        Validate JWT token and return payload if valid.

        Args:
            token (str): JWT token to validate
            verify_exp (bool): Whether to verify token expiration

        Returns:
            Optional[Dict]: Token payload if valid

        Raises:
            HTTPException: If token is invalid, expired, or blacklisted
        """
        try:
            logger.debug("Starting token validation")

            # Проверяем, не в черном ли списке токен
            if await self.is_token_blacklisted(token):
                logger.warning(f"Attempt to use blacklisted token")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been blacklisted",
                )

            # Декодируем токен с опциональной проверкой срока действия
            options = {
                "verify_signature": True,
                "verify_exp": verify_exp,
                "verify_iat": True,
                "require": ["exp", "iat", "jti"],
            }

            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                options=options,
            )

            # Проверяем наличие JTI
            if "jti" not in payload:
                logger.warning("Token without JTI detected")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token format: missing JTI",
                )

            logger.info(f"Token validated successfully. JTI: {payload['jti']}")
            return payload

        except jwt.ExpiredSignatureError as e:
            logger.warning(f"Expired token detected: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token detected: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format"
            )
        except jwt.PyJWTError as e:
            logger.error(f"JWT validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate token",
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token validation failed",
            )

    async def refresh_tokens(self, refresh_token: str) -> Tuple[str, str]:
        """Create new access and refresh tokens using refresh token"""
        payload = await self.validate_token(refresh_token)

        if payload["token_type"] != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        # Получаем актуальные данные пользователя из БД
        user_id = UUID(payload["user_id"])
        user = await self.user_repository.get_with_roles(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Помещаем использованный refresh token в черный список
        await self.blacklist_token(refresh_token)

        # Создаем новые токены с актуальными данными пользователя
        roles = [role.name for role in user.roles]
        new_access_token = await self.create_access_token(
            user_id=user.id,
            username=user.username,
            is_superuser=user.is_superuser,
            roles=roles,
        )
        new_refresh_token = await self.create_refresh_token(user.id)

        return new_access_token, new_refresh_token

    async def blacklist_token(self, token: str) -> None:
        """
        Add token to blacklist in Redis.
        Stores the token until its natural expiration time or minimum TTL.

        Args:
            token (str): JWT token to blacklist

        Raises:
            HTTPException: If token cannot be blacklisted in Redis
        """
        try:
            logger.debug("Starting token blacklisting process")

            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                options={"verify_exp": False},
            )

            # Проверяем наличие необходимых полей
            if not all(key in payload for key in ["exp", "jti"]):
                logger.error("Token missing required fields (exp or jti)")
                raise jwt.InvalidTokenError("Token missing required fields")

            # Вычисляем TTL
            exp_timestamp = payload["exp"]
            current_timestamp = datetime.now(UTC).timestamp()
            ttl = int(exp_timestamp - current_timestamp)
            min_ttl = 300  # 5 минут минимальное время хранения
            ttl = max(ttl, min_ttl)

            # Сохраняем в Redis
            try:
                jti = payload["jti"]
                redis_key = (
                    f"blacklist_token:{jti}"  # Используем JTI вместо полного токена
                )

                logger.debug(
                    f"Adding token with JTI {jti} to blacklist with TTL {ttl}s"
                )
                await self.redis_client.setex(redis_key, ttl, "1")

                logger.info(f"Token successfully blacklisted. JTI: {jti}, TTL: {ttl}s")

            except Exception as redis_error:
                logger.error(f"Redis error while blacklisting token: {redis_error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to blacklist token in Redis",
                )

        except jwt.InvalidTokenError as e:
            logger.warning(f"Attempted to blacklist invalid token: {str(e)}")
            return

        except Exception as e:
            logger.error(f"Unexpected error in blacklist_token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process token for blacklisting",
            )

    async def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if token is in the blacklist.

        Args:
            token (str): JWT token to check

        Returns:
            bool: True if token is blacklisted, False otherwise

        Raises:
            HTTPException: If there's an error checking the blacklist
        """
        try:
            logger.debug("Checking token blacklist status")

            # Декодируем токен для получения JTI
            try:
                payload = jwt.decode(
                    token,
                    self.config.secret_key,
                    algorithms=[self.config.algorithm],
                    options={"verify_exp": False},
                )

                # Проверяем наличие JTI
                if "jti" not in payload:
                    logger.warning("Token missing JTI field")
                    return False

                jti = payload["jti"]
                redis_key = f"blacklist_token:{jti}"

                # Проверяем наличие в черном списке
                is_blacklisted = await self.redis_client.exists(redis_key)

                if is_blacklisted:
                    logger.info(f"Token with JTI {jti} found in blacklist")
                else:
                    logger.debug(f"Token with JTI {jti} not found in blacklist")

                return bool(is_blacklisted)

            except jwt.InvalidTokenError as e:
                logger.warning(f"Invalid token provided for blacklist check: {str(e)}")
                return False

        except Exception as e:
            error_msg = "Error checking token blacklist status"
            logger.error(f"{error_msg}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
            )

    @circuit_protected
    async def create_tokens_for_user(self, user_id: Mapped[UUID]) -> Tuple[str, str]:
        """
        Create both access and refresh tokens for a user.

        Args:
            user_id (UUID): The unique identifier of the user

        Returns:
            Tuple[str, str]: A tuple containing (access_token, refresh_token)

        Raises:
            HTTPException: If user not found or token creation fails
        """
        try:
            logger.debug(f"Starting token creation for user ID: {user_id}")

            # Получаем пользователя с его ролями
            user = await self.user_repository.get_with_roles(user_id)

            if not user:
                logger.error(f"User not found for ID: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            # Подготавливаем роли пользователя
            roles = [role.name for role in user.roles]
            logger.debug(f"User roles: {roles}")

            try:
                # Создаем access token
                logger.debug(f"Creating access token for user: {user.username}")
                access_token = await self.create_access_token(
                    user_id=user.id,
                    username=user.username,
                    is_superuser=user.is_superuser,
                    roles=roles,
                )

                # Создаем refresh token
                logger.debug(f"Creating refresh token for user: {user.username}")
                refresh_token = await self.create_refresh_token(user.id)

                logger.info(
                    f"Tokens created successfully for user: {user.username} "
                    f"(ID: {user_id})"
                )

                return access_token, refresh_token

            except Exception as token_error:
                logger.error(
                    f"Failed to create tokens for user {user.username}: "
                    f"{str(token_error)}"
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create authentication tokens",
                )

        except HTTPException:
            # Пробрасываем HTTPException дальше
            raise
        except Exception as e:
            error_msg = f"Unexpected error during token creation for user ID {user_id}"
            logger.error(f"{error_msg}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
            )

    async def get_current_user(self, token: str) -> Optional[Dict]:
        """Get current user data from token"""
        payload = await self.validate_token(token)
        if not payload:
            return None

        user_id = UUID(payload["user_id"])
        user = await self.user_repository.get_with_roles(user_id)

        if not user:
            return None

        return {
            "id": user.id,
            "username": user.username,
            "is_superuser": user.is_superuser,
            "roles": [role.name for role in user.roles],
        }
