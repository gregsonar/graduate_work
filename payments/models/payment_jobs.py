# Нужна таблица payment_jobs для отслеживания статусов платежей.


from datetime import datetime, UTC
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

import uuid

Base = declarative_base()


class PaymentJob(Base):
    """Модель для хранения информации об автоплатежах.

    id – Уникальный идентификатор платежа
    subscription_id – ID подписки, к которой относится платёж
    payment_id – ID платежа в YooKassa
    status – Текущий статус платежа (pending, succeeded, failed и т. д.)
    created_at – Дата создания платежа
    updated_at – Последнее обновление статуса
    """

    __tablename__ = "payment_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=False)
    payment_id = Column(String, unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, succeeded, failed
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    def __repr__(self):
        return f"<PaymentJob {self.id} | Subscription {self.subscription_id} | Status {self.status}>"
