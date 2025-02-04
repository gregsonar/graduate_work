from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from db.postgres import Base
from models.mixins import TimeStampedMixin, UUIDMixin
from models.tariffs import TariffModel


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
    