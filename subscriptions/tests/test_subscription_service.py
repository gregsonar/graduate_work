from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from subscriptions.core.exceptions import (
    InvalidStatusTransitionException,
    SubscriptionNotFoundException
)
from subscriptions.models.subscription import (
    SubscriptionPlanType,
    SubscriptionStatus
)
from subscriptions.schemas.subscription_schema import SubscriptionCreate
from subscriptions.services.subscription_service import SubscriptionService
from subscriptions.services.validator import SubscriptionValidator


class TestSubscriptionService:
    @pytest.mark.asyncio
    async def test_create_subscription(self, db_session):
        service = SubscriptionService(db_session)
        subscription_data = SubscriptionCreate(
            user_id=uuid4(),
            plan_type=SubscriptionPlanType.BASIC,
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC) + timedelta(days=30),
            price=9.99,
            is_auto_renewable=True,
        )

        result = await service.create_subscription(subscription_data)
        assert result.user_id == subscription_data.user_id
        assert result.status == SubscriptionStatus.PENDING

    @pytest.mark.asyncio
    async def test_suspend_subscription(self, db_session, active_subscription):
        service = SubscriptionService(db_session)

        await service.suspend_subscription(active_subscription.id, "Payment failed")
        updated = await service.get_subscription(active_subscription.id)
        assert updated.status == SubscriptionStatus.SUSPENDED

    @pytest.mark.asyncio
    async def test_resume_subscription(self, db_session, active_subscription):
        service = SubscriptionService(db_session)

        # First suspend
        await service.suspend_subscription(active_subscription.id, "Payment failed")
        # Then resume
        await service.resume_subscription(active_subscription.id, "Payment resolved")

        updated = await service.get_subscription(active_subscription.id)
        assert updated.status == SubscriptionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_cancel_subscription(self, db_session, active_subscription):
        service = SubscriptionService(db_session)

        await service.cancel_subscription(
            active_subscription.id, "User requested", immediate=True
        )

        updated = await service.get_subscription(active_subscription.id)
        assert updated.status == SubscriptionStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_get_nonexistent_subscription(self, db_session):
        service = SubscriptionService(db_session)

        with pytest.raises(SubscriptionNotFoundException):
            await service.get_subscription(uuid4())

    @pytest.mark.asyncio
    async def test_invalid_status_transition(self, db_session, active_subscription):
        service = SubscriptionService(db_session)

        # First cancel
        await service.cancel_subscription(active_subscription.id, "Test cancel", True)

        # Try to suspend cancelled subscription
        with pytest.raises(InvalidStatusTransitionException):
            await service.suspend_subscription(active_subscription.id, "Test suspend")
