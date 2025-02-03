from enum import Enum

from sqlalchemy import Column, ForeignKey, Enum as SQLEnum, DateTime, String, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from subscriptions.models.base_models import Base


class SubscriptionType(str, Enum):
    BASIC = 'basic'
    STANDARD = 'standard'
    PREMIUM = 'premium'


class SubscriptionStatus(str, Enum):
    ACTIVE = 'active'
    PENDING = 'pending'
    CANCELED = 'canceled'
    EXPIRED = 'expired'
    SUSPENDED = 'suspended'


class UserSubscription(Base):
    __tablename__ = 'user_subscriptions'

    user_id = Column(UUID(as_uuid=True), nullable=False)
    subscription_type = Column(SQLEnum(SubscriptionType), nullable=False)
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.PENDING)

    # Даты
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Платежная информация
    payment_method_id = Column(String(100))  # ID метода оплаты (для интеграции с платежной системой)
    auto_renewal = Column(Boolean, default=False)
    last_payment_date = Column(DateTime)
    next_payment_date = Column(DateTime)

    __table_args__ = (
        # Индексы для оптимизации запросов
        Index('idx_user_subscriptions_user_id', 'user_id'),
        Index('idx_user_subscriptions_status', 'status'),
        Index('idx_user_subscriptions_end_date', 'end_date'),
    )


class UserSubscriptionHistory(Base):
    __tablename__ = 'user_subscription_history'

    user_subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey('user_subscriptions.id', ondelete='CASCADE'),
        nullable=False
    )
    action = Column(String(50), nullable=False)  # create, update, cancel, renew
    subscription_type = Column(SQLEnum(SubscriptionType))
    status = Column(SQLEnum(SubscriptionStatus))

    __table_args__ = (
        Index('idx_subscription_history_user_subscription_id', 'user_subscription_id'),
    )