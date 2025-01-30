from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped

from auth.db.postgres import Base
from .base_models import TimestampMixin


class UserRole(Base, TimestampMixin):
    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    role_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    assigned_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_by: Mapped[Optional[uuid.UUID]] = Column(UUID(as_uuid=True), ForeignKey('users.id'))

    __table_args__ = (
        Index('ix_user_roles_user_id', 'user_id'),
        Index('ix_user_roles_role_id', 'role_id'),
        Index('ix_user_roles_assigned_by', 'assigned_by'),
    )

    def __repr__(self) -> str:
        return f"<UserRole user_id={self.user_id} role_id={self.role_id}>"