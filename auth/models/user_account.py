from __future__ import annotations
import uuid
from enum import Enum
from typing import List, Optional
from datetime import datetime, timedelta

from sqlalchemy import Boolean, Column, String, Index, JSON, ForeignKey, Enum as SQLEnum, DateTime, text, \
    PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from werkzeug.security import check_password_hash, generate_password_hash

from auth.db.postgres import Base
from .base_models import TimestampMixin, SocialProvider


def create_partition(target, connection, **kw) -> None:
    """Creating partitions for user_social_accounts table"""
    for provider in SocialProvider:
        provider_partition = f"user_social_accounts_{provider.value.lower()}"

        connection.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {provider_partition} 
            PARTITION OF user_social_accounts
            FOR VALUES IN ('{provider.value}')
            PARTITION BY RANGE (created_at)
        """))

        current_date = datetime.now().date().replace(day=1)
        for _ in range(12):
            next_month = (current_date + timedelta(days=32)).replace(day=1)
            time_partition = f"{provider_partition}_{current_date.strftime('%Y_%m')}"

            connection.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {time_partition} 
                PARTITION OF {provider_partition}
                FOR VALUES FROM ('{current_date}') TO ('{next_month}')
            """))
            current_date = next_month

class UserSocialAccount(Base, TimestampMixin):
    __tablename__ = "user_social_accounts"

    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    provider: Mapped[SocialProvider] = Column(SQLEnum(SocialProvider), nullable=False)
    social_id: Mapped[str] = Column(String(255), nullable=False)
    social_username: Mapped[Optional[str]] = Column(String(255), nullable=True)
    social_email: Mapped[Optional[str]] = Column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = Column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = Column(String(100), nullable=True)
    avatar_url: Mapped[Optional[str]] = Column(String(500), nullable=True)
    access_token: Mapped[Optional[str]] = Column(String(500), nullable=True)
    refresh_token: Mapped[Optional[str]] = Column(String(500), nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    is_primary: Mapped[bool] = Column(Boolean, default=False)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="user_social_accounts")

    __table_args__ = (
        PrimaryKeyConstraint('id', 'provider', 'created_at'),
        Index('ix_user_social_accounts_provider_social_id', 'provider', 'social_id', 'created_at', unique=True),
        Index('ix_user_social_accounts_user_id', 'user_id', 'provider', 'created_at'),
        {
            # Сначала партиционируем по provider
            'postgresql_partition_by': 'LIST (provider)',
            'listeners': [('after_create', create_partition)],
        }
    )

    def __init__(self, user_id: uuid.UUID, provider: SocialProvider, social_id: str, **kwargs):
        self.user_id = user_id
        self.provider = provider
        self.social_id = social_id
        self.social_username = kwargs.get('social_username')
        self.social_email = kwargs.get('social_email')
        self.first_name = kwargs.get('first_name')
        self.last_name = kwargs.get('last_name')
        self.avatar_url = kwargs.get('avatar_url')
        self.access_token = kwargs.get('access_token')
        self.refresh_token = kwargs.get('refresh_token')
        self.token_expires_at = kwargs.get('token_expires_at')
        self.metadata = kwargs.get('metadata', {})
        self.is_primary = kwargs.get('is_primary', False)