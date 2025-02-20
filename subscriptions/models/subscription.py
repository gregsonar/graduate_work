from enum import Enum
from sqlalchemy import Column, ForeignKey, Boolean, Numeric, String, Enum as SQLEnum, DateTime, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from subscriptions.models.base_models import Base

class SubscriptionPlanType(str, Enum):
    BASIC = 'basic'
    STANDARD = 'standard'
    PREMIUM = 'premium'

class SubscriptionStatus(str, Enum):
    ACTIVE = 'active'
    PENDING = 'pending'
    CANCELED = 'canceled'
    EXPIRED = 'expired'
    SUSPENDED = 'suspended'

class SubscriptionPlan(Base):
    __tablename__ = 'subscription_plans'
    name = Column(String(50), nullable=False)
    plan_type = Column(SQLEnum(SubscriptionPlanType), nullable=False, unique=True)
    description = Column(String(500))
    price = Column(Numeric(10, 2), nullable=False)
    duration_days = Column(Integer, nullable=False)
    features = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)
    # subscriptions = relationship("Subscription", back_populates="plan")

class Subscription(Base):

    __tablename__ = 'subscriptions'
    user_id = Column(UUID(as_uuid=True), nullable=False)
    plan_type = Column(SQLEnum(SubscriptionPlanType), nullable=False)
    status = Column(SQLEnum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.PENDING)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    is_auto_renewable = Column(Boolean, default=False)
    plan_id = Column(UUID(as_uuid=True), nullable=True)
    # plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    history = relationship("SubscriptionHistory", back_populates="subscription", cascade="all, delete-orphan")
    user_subscriptions = relationship("UserSubscription", back_populates="subscription")

class SubscriptionHistory(Base):
    __tablename__ = 'subscription_history'
    subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey('subscriptions.id', ondelete='CASCADE'),
        nullable=False
    )
    action = Column(String(50), nullable=False)
    details = Column(JSONB, default={})
    subscription = relationship("Subscription", back_populates="history")