from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import Boolean, Column, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from auth.db.postgres import Base

from .access_log import AccessLog
from .base_models import SocialProvider, TimestampMixin
from .role import Role
from .user_account import UserSocialAccount
from .user_role import UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    username: Mapped[str] = Column(String(150), unique=True, nullable=False)
    email: Mapped[Optional[str]] = Column(String(255), unique=True, nullable=True)
    password_hash: Mapped[Optional[str]] = Column(String(255), nullable=True)
    is_superuser: Mapped[bool] = Column(Boolean, default=False)
    is_active: Mapped[bool] = Column(Boolean, default=True)
    display_name: Mapped[Optional[str]] = Column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = Column(String(500), nullable=True)

    # Relationships
    user_social_accounts: Mapped[List["UserSocialAccount"]] = relationship(
        "UserSocialAccount", back_populates="user", cascade="all, delete-orphan"
    )

    access_logs: Mapped[List["AccessLog"]] = relationship(
        "AccessLog", back_populates="user"
    )

    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary="user_roles",
        primaryjoin="User.id == UserRole.user_id",
        secondaryjoin="UserRole.role_id == Role.id",
        back_populates="users",
    )

    assigned_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole", foreign_keys="UserRole.assigned_by"
    )

    __table_args__ = (
        Index("ix_users_username", "username"),
        Index("ix_users_email", "email"),
    )

    def __init__(
        self,
        username: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        is_superuser: bool = False,
        avatar_url: Optional[str] = None,
    ):
        self.username = username
        self.email = email
        self.avatar_url = avatar_url
        if password:
            self.set_password(password)
        self.is_superuser = is_superuser

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def add_social_account(
        self,
        provider: SocialProvider,
        social_id: str,
        is_primary: bool = False,
        **social_data,
    ) -> UserSocialAccount:
        """Добавляет новый социальный аккаунт пользователю"""
        if is_primary and not self.password_hash:
            # Если это первичный метод аутентификации и у пользователя нет пароля
            social_data["is_primary"] = True

        social_account = UserSocialAccount(
            user_id=self.id, provider=provider, social_id=social_id, **social_data
        )
        self.social_accounts.append(social_account)

        # Обновляем данные пользователя из социального аккаунта
        if not self.display_name and social_data.get("first_name"):
            self.display_name = f"{social_data.get('first_name')} {social_data.get('last_name', '')}".strip()
        if not self.avatar_url and social_data.get("avatar_url"):
            self.avatar_url = social_data.get("avatar_url")

        return social_account

    def remove_social_account(self, provider: SocialProvider) -> None:
        """Удаляет социальный аккаунт пользователя"""
        account = next(
            (acc for acc in self.social_accounts if acc.provider == provider), None
        )
        if account:
            if account.is_primary and not self.password_hash:
                raise ValueError(
                    "Cannot remove primary authentication method without setting a password first"
                )
            self.social_accounts.remove(account)

    def get_social_account(
        self, provider: SocialProvider
    ) -> Optional[UserSocialAccount]:
        """Получает социальный аккаунт по провайдеру"""
        return next(
            (acc for acc in self.social_accounts if acc.provider == provider), None
        )

    def has_social_provider(self, provider: SocialProvider) -> bool:
        """Проверяет, есть ли у пользователя аккаунт указанного провайдера"""
        return any(acc.provider == provider for acc in self.social_accounts)

    def get_display_name(self) -> str:
        """Возвращает отображаемое имя пользователя"""
        return self.display_name or self.username

    def has_role(self, role_name: str) -> bool:
        """Проверяет наличие роли у пользователя"""
        return any(role.name == role_name for role in self.roles)

    def __repr__(self) -> str:
        return f"<User {self.username}>"
