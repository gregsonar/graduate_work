from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, DateTime, Text, Index, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship, Mapped

from auth.db.postgres import Base
from .base_models import TimestampMixin


class AccessLog(Base, TimestampMixin):
    __tablename__ = "access_logs"

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    ip_address: Mapped[str] = Column(INET)
    user_agent: Mapped[str] = Column(Text)
    accessed_at: Mapped[datetime] = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="access_logs")

    __table_args__ = (
        Index("ix_access_logs_user_id", "user_id"),
        Index("ix_access_logs_accessed_at", "accessed_at"),
        Index("ix_access_logs_ip_address", "ip_address"),
    )

    def __init__(self, user_id: uuid.UUID, ip_address: str, user_agent: str) -> None:
        self.user_id = user_id
        self.ip_address = ip_address
        self.user_agent = user_agent

    def __repr__(self) -> str:
        return f"<AccessLog user_id={self.user_id} ip={self.ip_address}>"
