from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped


class TimestampMixin:
    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class CRUDMixin:
    @declared_attr
    def is_active(cls) -> Mapped[bool]:
        return Column(Boolean, default=True, nullable=False)

    @declared_attr
    def is_deleted(cls) -> Mapped[bool]:
        return Column(Boolean, default=False, nullable=False)


class SocialProvider(str, Enum):
    VK = "vk"
    YANDEX = "yandex"
