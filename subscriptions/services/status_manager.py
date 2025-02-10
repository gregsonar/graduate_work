from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from subscriptions.services.interfaces import ISubscriptionStatusManager
from subscriptions.services.repository import SubscriptionRepository
from subscriptions.models.subscription import SubscriptionStatus
from subscriptions.services.validator import SubscriptionValidator


class SubscriptionStatusManager(ISubscriptionStatusManager):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = SubscriptionRepository(session)
        self.validator = SubscriptionValidator()  # Добавляем валидатор

    async def suspend(self, subscription_id: UUID, reason: str) -> None:
        subscription = await self.repository.get(subscription_id)
        await self.validator.validate_status_transition(
            subscription.status,
            SubscriptionStatus.SUSPENDED
        )
        await self.repository.update(subscription_id, {
            'status': SubscriptionStatus.SUSPENDED
        })

    async def resume(self, subscription_id: UUID, comment: str | None) -> None:
        subscription = await self.repository.get(subscription_id)
        await self.validator.validate_status_transition(
            subscription.status,
            SubscriptionStatus.ACTIVE
        )
        await self.repository.update(subscription_id, {
            'status': SubscriptionStatus.ACTIVE
        })

    async def cancel(self, subscription_id: UUID, reason: str, immediate: bool) -> None:
        subscription = await self.repository.get(subscription_id)
        await self.validator.validate_status_transition(
            subscription.status,
            SubscriptionStatus.CANCELED
        )
        await self.repository.update(subscription_id, {
            'status': SubscriptionStatus.CANCELED
        })