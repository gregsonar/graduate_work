from enum import Enum

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from billing.src.db.postgres import Base
from billing.src.models.mixins import TimeStampedMixin, UUIDMixin
from billing.src.models.tariffs import TariffModel


class PaymentModel(Base, UUIDMixin, TimeStampedMixin):
    """Модель определяющая платеж."""

    __tablename__ = 'payment'

    user_id = Column(UUID, nullable=False)
    tariff_id = Column(
        ForeignKey(TariffModel.id, ondelete="SET NULL"),
        nullable=False,
    )
    status = Column(String)
    payment_method_id = Column(UUID, nullable=False)
    payment_id = Column(UUID, nullable=False)

class PaymentStatus(Enum):
    SUCCEEDED = 'succeeded'
    PENDING = 'pending'
    CANCELED = 'canceled'

    def __repr__(self):
        return self.value

    def __str__(self):
        return str(self.value)
