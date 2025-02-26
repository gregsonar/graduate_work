from sqlalchemy import Boolean, Column, Integer, Numeric, String, Text

from billing.src.db.postgres import Base
from billing.src.models.mixins import TimeStampedMixin, UUIDMixin


class TariffModel(Base, UUIDMixin, TimeStampedMixin):
    """Модель тарифа"""

    __tablename__ = "tariff"

    name = Column(String(255))
    description = Column(Text, nullable=True)
    price = Column(Numeric(6, 2), nullable=False)
    currency = Column(String(3))
    duration = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
