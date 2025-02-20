from enum import Enum

from billing.src.db.postgres import Base
from billing.src.models.mixins import TimeStampedMixin, UUIDMixin
from billing.src.models.tariffs import TariffModel
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID


class PaymentModel(Base, UUIDMixin, TimeStampedMixin):
    """Модель определяющая платеж."""

    __tablename__ = 'payment'

    user_id = Column(UUID, nullable=False)
    tariff_id = Column(
        ForeignKey(TariffModel.id, ondelete="SET NULL"),
        nullable=False,
    )
    status = Column(String)
    payment_id = Column(UUID, nullable=False)
    subscription_id = Column(UUID, nullable=False)
    method_id = Column(UUID, nullable=True)

    def __repr__(self):
        return f'<PaymentModel {self.id}>'

    def __init__(self, user_id, tariff_id, status, payment_id, subscription_id, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.tariff_id = tariff_id
        self.status = status
        self.payment_id = payment_id
        self.subscription_id = subscription_id




class PaymentStatus(Enum):
    SUCCEEDED = 'succeeded'
    PENDING = 'pending'
    CANCELED = 'canceled'
    WAITING_FOR_CAPTURE = 'waiting_for_capture'

    def __repr__(self):
        return self.value

    def __str__(self):
        return str(self.value)
