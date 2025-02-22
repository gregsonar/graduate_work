from billing.src.db.postgres import Base
from billing.src.models.mixins import TimeStampedMixin, UUIDMixin
from sqlalchemy import Column, Numeric, String
from sqlalchemy.dialects.postgresql import UUID


class RefundModel(Base, UUIDMixin, TimeStampedMixin):
    """Модель возврата стоимости подписки."""

    __tablename__ = "refund"

    payment_id = Column(String, nullable=False)
    refund_id = Column(UUID, nullable=False)
    amount = Column(Numeric(6, 2), nullable=False)
    status = Column(String, nullable=False)
