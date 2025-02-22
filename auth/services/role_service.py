import logging
import uuid
from typing import Type, Dict, Any, List

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from auth.db.postgres import get_session
from auth.models.role import Role
from auth.models.user import User
from auth.models.user_role import UserRole

logger = logging.getLogger(__name__)

from auth.db.crud import RoleRepository, UserRoleRepository


class RoleService(RoleRepository):
    def __init__(self, session: AsyncSession = Depends(get_session)):
        super().__init__(session)
        self.user_role_repository = UserRoleRepository(session)

    async def get_all(self, skip: int = 0, limit: int = 100, **kwargs) -> List[Role]:
        stmt = (
            select(self.model)
            .options(selectinload(self.model.users))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, obj_id: uuid.UUID, **kwargs) -> Role | None:
        stmt = (
            select(self.model)
            .options(selectinload(self.model.users))
            .where(self.model.id == obj_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def give_role_to_user(self, user_id: uuid.UUID, role_id: uuid.UUID) -> bool:

        try:
            # Проверяем существование роли
            role = await self.get_by_id(role_id)
            if not role:
                logger.error(f"Role {role_id} not found")
                return False

            # Проверяем существование пользователя через запрос
            stmt = select(User).where(User.id == user_id)
            result = await self.session.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                logger.error(f"User {user_id} not found")
                return False

            # Проверяем, есть ли уже такая роль у пользователя
            existing_roles = await self.user_role_repository.get_user_roles(user_id)
            if any(ur.role_id == role_id for ur in existing_roles):
                logger.info(f"User {user_id} already has role {role_id}")
                return True

            # Используем метод из UserRoleRepository для назначения роли
            await self.user_role_repository.assign_role(user_id, role_id)
            logger.info(f"Successfully assigned role {role_id} to user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error assigning role to user: {str(e)}")
            await self.session.rollback()
            return False

    async def delete_role_from_user(
        self, user_id: uuid.UUID, role_id: uuid.UUID
    ) -> bool:
        try:

            # Находим запись о роли пользователя
            stmt = select(UserRole).where(
                and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
            )
            result = await self.session.execute(stmt)
            user_role = result.scalar_one_or_none()

            if not user_role:
                logger.warning(f"Role {role_id} not found for user {user_id}")
                return False

            # Удаляем роль
            await self.session.delete(user_role)
            await self.session.commit()

            logger.info(f"Successfully removed role {role_id} from user {user_id}")
            return True

        except ValueError as ve:
            logger.error(f"Invalid UUID format: {str(ve)}")
            return False
        except Exception as e:
            logger.error(f"Error removing role from user: {str(e)}")
            await self.session.rollback()
            return False

    async def get_all_users_with_roles(self, role_id: uuid.UUID) -> List[User]:
        try:
            # Проверяем существование роли используя метод из базового репозитория
            role = await self.get_by_id(role_id)
            if not role:
                logger.error(f"Role {role_id} not found")
                return []

            # Получаем всех пользователей с указанной ролью
            stmt = (
                select(User)
                .join(UserRole, User.id == UserRole.user_id)
                .where(UserRole.role_id == role_id)
            )

            result = await self.session.execute(stmt)
            users = result.scalars().all()

            return list(users)

        except Exception as e:
            logger.error(f"Error getting users with role: {str(e)}")
            return []

    async def get_users_by_role(self, role_id: uuid.UUID) -> List[dict]:
        """
        Получает список пользователей с определенной ролью в формате словаря
        """
        try:
            users = await self.get_all_users_with_roles(role_id)
            return [
                {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_active,
                }
                for user in users
            ]
        except Exception as e:
            logger.error(f"Error getting users by role: {str(e)}")
            return []

    async def get_user_roles(self, user_id: uuid.UUID) -> List[Role]:
        """
        Получает список ролей пользователя с предварительной загрузкой связанных пользователей
        """
        try:
            # Проверяем существование пользователя
            stmt = select(User).where(User.id == user_id)
            result = await self.session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"User {user_id} not found")
                return []

            # Получаем роли пользователя с предварительной загрузкой пользователей
            stmt = (
                select(Role)
                .options(selectinload(Role.users))
                .join(UserRole, Role.id == UserRole.role_id)
                .where(
                    and_(
                        UserRole.user_id == user_id,
                        Role.is_deleted == False,
                        Role.is_active == True,
                    )
                )
                .order_by(Role.name)
            )

            result = await self.session.execute(stmt)
            roles = result.unique().scalars().all()

            return list(roles)

        except Exception as e:
            logger.error(f"Error getting user roles: {str(e)}")
            return []
