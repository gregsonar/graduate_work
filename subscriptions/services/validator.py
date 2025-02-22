from datetime import datetime
from typing import Dict, Set

from subscriptions.models.subscription import SubscriptionStatus
from subscriptions.services.interfaces import ISubscriptionValidator
from subscriptions.core.exceptions import InvalidStatusTransitionException


class SubscriptionValidator(ISubscriptionValidator):
    # Все возможные переходы статусов подписки
    ALLOWED_TRANSITIONS: Dict[SubscriptionStatus, Set[SubscriptionStatus]] = {
        SubscriptionStatus.PENDING: {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.CANCELED,
        },
        SubscriptionStatus.ACTIVE: {
            SubscriptionStatus.SUSPENDED,
            SubscriptionStatus.CANCELED,
            SubscriptionStatus.EXPIRED,
        },
        SubscriptionStatus.SUSPENDED: {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.CANCELED,
        },
        SubscriptionStatus.CANCELED: set(),
        SubscriptionStatus.EXPIRED: {SubscriptionStatus.ACTIVE},
    }

    async def validate_status_transition(
        self, current_status: str, new_status: str
    ) -> bool:
        current = SubscriptionStatus(current_status)
        new = SubscriptionStatus(new_status)

        if new not in self.ALLOWED_TRANSITIONS[current]:
            raise InvalidStatusTransitionException(current_status, new_status)
        return True

    async def validate_dates(self, start_date: datetime, end_date: datetime) -> bool:
        if start_date >= end_date:
            raise ValueError("End date must be after start date")
        if start_date.date() < datetime.now().date():
            raise ValueError("Start date cannot be in the past")
        return True

    async def validate_subscription_period(
        self, plan_duration_days: int, start_date: datetime, end_date: datetime
    ) -> bool:
        """Проверяет соответствие периода подписки длительности плана"""
        duration = (end_date - start_date).days
        if duration != plan_duration_days:
            raise ValueError(f"Subscription period must be {plan_duration_days} days")
        return True
