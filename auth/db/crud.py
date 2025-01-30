# auth/db/crud.py
from uuid import UUID
from datetime import datetime
from typing import Type, TypeVar, Generic, Optional, List, Dict, Any

from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, Mapped

from auth.models.base_models import SocialProvider
from auth.models.user import User
from auth.models.role import Role
from auth.models.access_log import AccessLog
from auth.models.user_account import UserSocialAccount
from auth.models.user_role import UserRole

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(
        self, obj_id: UUID, load_related: bool = False
    ) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == obj_id)
        if load_related:
            stmt = stmt.options(selectinload("*"))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        load_related: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        stmt = select(self.model).offset(skip).limit(limit)
        if load_related:
            stmt = stmt.options(selectinload("*"))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, obj_data: Dict[str, Any]) -> ModelType:
        obj = self.model(**obj_data)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(
        self, obj_id: UUID, data: Dict[str, Any]
    ) -> Optional[ModelType]:
        stmt = (
            update(self.model)
            .where(self.model.id == obj_id)
            .values(**data)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def delete(self, obj_id: UUID) -> bool:
        stmt = delete(self.model).where(self.model.id == obj_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def get_filtered(
        self,
        filters: Dict[str, Any],
        load_related: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        conditions = [
            getattr(self.model, key) == value
            for key, value in filters.items()
        ]
        stmt = (
            select(self.model)
            .where(and_(*conditions))
            .offset(skip)
            .limit(limit)
        )
        if load_related:
            stmt = stmt.options(selectinload("*"))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, filters: Dict[str, Any] = None) -> int:

        try:
            stmt = select(func.count()).select_from(self.model)

            if filters:
                conditions = [
                    getattr(self.model, key) == value
                    for key, value in filters.items()
                ]
                stmt = stmt.where(and_(*conditions))

            result = await self.session.execute(stmt)
            return result.scalar_one()

        except Exception as e:
            # Логируем ошибку, но возвращаем 0 вместо исключения
            # чтобы не прерывать работу приложения при подсчете
            return 0


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(self.model).where(self.model.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(self.model).where(self.model.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_roles(self, user_id: Mapped[UUID]) -> Optional[User]:
        stmt = (
            select(self.model)
            .where(self.model.id == user_id)
            .options(selectinload(self.model.roles))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class RoleRepository(BaseRepository[Role]):
    def __init__(self, session: AsyncSession):
        super().__init__(Role, session)

    async def get_by_name(self, name: str) -> Optional[Role]:
        stmt = (
            select(self.model)
            .options(selectinload(self.model.users))
            .where(self.model.name == name)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_roles(self) -> List[Role]:
        stmt = (
            select(self.model)
            .options(selectinload(self.model.users))  # Всегда загружаем пользователей
            .where(
                and_(
                    self.model.is_active == True,
                    self.model.is_deleted == False
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class UserRoleRepository(BaseRepository[UserRole]):
    def __init__(self, session: AsyncSession):
        super().__init__(UserRole, session)

    async def get_user_roles(self, user_id: UUID) -> List[UserRole]:
        stmt = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def assign_role(
        self, user_id: UUID, role_id: UUID, assigned_by: Optional[UUID] = None
    ) -> UserRole:
        user_role_data = {
            "user_id": user_id,
            "role_id": role_id,
            "assigned_by": assigned_by
        }
        return await self.create(user_role_data)


class AccessLogRepository(BaseRepository[AccessLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(AccessLog, session)

    async def get_user_logs(
        self, user_id: UUID, page: int = 1, page_size: int = 10
    ) -> List[AccessLog]:
        offset = (page - 1) * page_size
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.accessed_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


    async def create_log(
        self, user_id: Mapped[UUID], ip_address: str, user_agent: str
    ) -> AccessLog:
        log_data = {
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        return await self.create(log_data)

class SocialAccountRepository(BaseRepository[UserSocialAccount]):
    def __init__(self, session: AsyncSession):
        super().__init__(UserSocialAccount, session)

    async def get_by_provider_and_social_id(
        self,
        provider: SocialProvider,
        social_id: str
    ) -> Optional[UserSocialAccount]:
        """Получение социального аккаунта по провайдеру и social_id"""
        stmt = select(self.model).where(
            self.model.provider == provider,
            self.model.social_id == social_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_accounts(
        self,
        user_id: UUID,
        provider: Optional[SocialProvider] = None
    ) -> List[UserSocialAccount]:
        """Получение всех социальных аккаунтов пользователя"""
        stmt = select(self.model).where(self.model.user_id == user_id)
        if provider:
            stmt = stmt.where(self.model.provider == provider)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_primary_account(
        self,
        user_id: UUID
    ) -> Optional[UserSocialAccount]:
        """Получение основного социального аккаунта пользователя"""
        stmt = select(self.model).where(
            self.model.user_id == user_id,
            self.model.is_primary == True
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()