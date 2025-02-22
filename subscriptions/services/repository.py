from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from subscriptions.models.subscription import Subscription, SubscriptionStatus
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

    async def get_with_user_id(self, user_id: UUID) -> Subscription:
        result = await self.session.execute(
            select(Subscription).filter(Subscription.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()
        if not subscription:
            raise SubscriptionNotFoundException()
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

    async def list_subscriptions(
        self,
        offset: int = 0,
        limit: int = 50,
        user_id: Optional[UUID] = None,
        status: Optional[SubscriptionStatus] = None,
        plan_type: Optional[str] = None,
        end_date: Optional[datetime.date] = None,
        # добавляем фильтр по дате платежа/отмены подписки
    ) -> List[Subscription]:

        query = select(Subscription)

        # Build filter conditions
        conditions = []
        if user_id:
            conditions.append(Subscription.user_id == user_id)
        if status:
            conditions.append(Subscription.status == status)
        if plan_type:
            conditions.append(Subscription.plan_type == plan_type)
        if end_date:
            conditions.append(Subscription.end_date >= end_date)
            conditions.append(Subscription.end_date < (end_date + timedelta(days=1)))

        if conditions:
            query = query.filter(and_(*conditions))

        # Add pagination
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await self.session.execute(query)
        return list(result.scalars().all())
