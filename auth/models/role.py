from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from auth.db.postgres import Base

from .base_models import CRUDMixin, TimestampMixin


class Role(Base, TimestampMixin, CRUDMixin):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = Column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = Column(Text)

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_roles",
        primaryjoin="Role.id == UserRole.role_id",
        secondaryjoin="UserRole.user_id == User.id",
        back_populates="roles",
    )

    __table_args__ = (
        Index("ix_roles_name", "name"),
        Index("ix_roles_is_active", "is_active"),
        Index("ix_roles_is_deleted", "is_deleted"),
    )

    def __init__(
        self, name: str, description: Optional[str] = None, id: Optional[UUID] = None
    ) -> None:
        super().__init__()
        self.name = name
        self.description = description
        if id is not None:
            self.id = id

    @classmethod
    def get_active(cls) -> List[Role]:
        return cls.query.filter_by(is_active=True, is_deleted=False).all()

    @classmethod
    def get_by_name(cls, name: str) -> Optional[Role]:
        return cls.query.filter_by(name=name, is_deleted=False).first()

    def update(
        self, name: Optional[str] = None, description: Optional[str] = None
    ) -> None:
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        self.updated_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<Role {self.name}>"
