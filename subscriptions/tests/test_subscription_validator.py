import pytest
from datetime import datetime, timedelta, UTC
from subscriptions.services.validator import SubscriptionValidator
from subscriptions.models.subscription import SubscriptionStatus
from subscriptions.core.exceptions import (
    InvalidStatusTransitionException
)



class TestSubscriptionValidator:
    @pytest.mark.asyncio
    async def test_valid_status_transition(self):
        validator = SubscriptionValidator()
        result = await validator.validate_status_transition(
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.SUSPENDED
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_invalid_status_transition(self):
        validator = SubscriptionValidator()
        with pytest.raises(InvalidStatusTransitionException):
            await validator.validate_status_transition(
                SubscriptionStatus.CANCELLED,
                SubscriptionStatus.ACTIVE
            )

    @pytest.mark.asyncio
    async def test_validate_dates(self):
        validator = SubscriptionValidator()
        start_date = datetime.now(UTC) + timedelta(days=1)
        end_date = start_date + timedelta(days=30)

        result = await validator.validate_dates(start_date, end_date)
        assert result is True

    @pytest.mark.asyncio
    async def test_invalid_dates(self):
        validator = SubscriptionValidator()
        start_date = datetime.now(UTC) + timedelta(days=30)
        end_date = datetime.now(UTC)

        with pytest.raises(ValueError, match="End date must be after start date"):
            await validator.validate_dates(start_date, end_date)