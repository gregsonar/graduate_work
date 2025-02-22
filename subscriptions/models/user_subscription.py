from enum import Enum

from sqlalchemy import (
    Column,
    ForeignKey,
    Enum as SQLEnum,
    DateTime,
    String,
    Boolean,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from subscriptions.models.base_models import Base
from subscriptions.models.subscription import Subscription, SubscriptionStatus


class SubscriptionType(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    user_id = Column(UUID(as_uuid=True), nullable=False)
    subscription_type = Column(SQLEnum(SubscriptionType), nullable=False)
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.PENDING)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    payment_method_id = Column(String(100))
    auto_renewal = Column(Boolean, default=False)
    last_payment_date = Column(DateTime)
    next_payment_date = Column(DateTime)
    subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    subscription = relationship("Subscription", back_populates="user_subscriptions")
    history = relationship(
        "UserSubscriptionHistory",
        back_populates="user_subscription",
        cascade="all, delete-orphan",
    )
    __table_args__ = (
        Index("idx_user_subscriptions_user_id", "user_id"),
        Index("idx_user_subscriptions_status", "status"),
        Index("idx_user_subscriptions_end_date", "end_date"),
    )


class UserSubscriptionHistory(Base):
    __tablename__ = "user_subscription_history"
    user_subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
    )
    action = Column(String(50), nullable=False)
    subscription_type = Column(SQLEnum(SubscriptionType))
    status = Column(SQLEnum(SubscriptionStatus))
    user_subscription = relationship("UserSubscription", back_populates="history")
    __table_args__ = (
        Index("idx_subscription_history_user_subscription_id", "user_subscription_id"),
    )
