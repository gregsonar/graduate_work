from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from subscriptions.models.subscription import Subscription
from subscriptions.services.interfaces import ISubscriptionRepository
from subscriptions.core.exceptions import SubscriptionNotFoundException

class SubscriptionRepository(ISubscriptionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, subscription_data: dict) -> Subscription:
        subscription = Subscription(**subscription_data)
        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription

    async def get(self, subscription_id: UUID) -> Subscription:
        result = await self.session.execute(
            select(Subscription).filter(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()
        if not subscription:
            raise SubscriptionNotFoundException()
        return subscription

    async def update(self, subscription_id: UUID, data: dict) -> Subscription:
        subscription = await self.get(subscription_id)
        for key, value in data.items():
            setattr(subscription, key, value)
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription
