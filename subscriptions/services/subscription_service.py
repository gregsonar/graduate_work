from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from subscriptions.schemas.subscription_schema import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    SubscriptionHistoryResponse
)
from subscriptions.services.repository import SubscriptionRepository
from subscriptions.services.status_manager import SubscriptionStatusManager
from subscriptions.services.history_manager import SubscriptionHistoryManager

class SubscriptionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = SubscriptionRepository(session)
        self.status_manager = SubscriptionStatusManager(session)
        self.history_manager = SubscriptionHistoryManager(session)

    async def create_subscription(self, subscription_data: SubscriptionCreate) -> SubscriptionResponse:
        subscription = await self.repository.create(subscription_data.model_dump())
        await self.history_manager.add_record(
            subscription.id,
            "created",
            {"plan_type": subscription.plan_type}
        )
        return SubscriptionResponse.model_validate(subscription)

    async def get_subscription(self, subscription_id: UUID) -> SubscriptionResponse:
        subscription = await self.repository.get(subscription_id)
        return SubscriptionResponse.model_validate(subscription)

    async def get_subscription_with_user_id(self, user_id: UUID) -> SubscriptionResponse:
        subscription = await self.repository.get_with_user_id(user_id)
        return SubscriptionResponse.model_validate(subscription)

    async def update_subscription(
        self,
        subscription_id: UUID,
        update_data: SubscriptionUpdate
    ) -> SubscriptionResponse:
        subscription = await self.repository.update(
            subscription_id,
            update_data.model_dump(exclude_none=True)
        )
        await self.history_manager.add_record(
            subscription_id,
            "updated",
            update_data.model_dump(exclude_none=True)
        )
        return SubscriptionResponse.model_validate(subscription)

    async def suspend_subscription(self, subscription_id: UUID, reason: str) -> None:
        await self.status_manager.suspend(subscription_id, reason)
        await self.history_manager.add_record(
            subscription_id,
            "suspended",
            {"reason": reason}
        )

    async def resume_subscription(self, subscription_id: UUID, comment: str | None) -> None:
        await self.status_manager.resume(subscription_id, comment)
        await self.history_manager.add_record(
            subscription_id,
            "resumed",
            {"comment": comment} if comment else None
        )

    async def cancel_subscription(
        self,
        subscription_id: UUID,
        reason: str,
        immediate: bool
    ) -> None:
        await self.status_manager.cancel(subscription_id, reason, immediate)
        await self.history_manager.add_record(
            subscription_id,
            "cancelled",
            {"reason": reason, "immediate": immediate}
        )

    async def get_subscription_history(
        self,
        subscription_id: UUID
    ) -> list[SubscriptionHistoryResponse]:
        return await self.history_manager.get_history(subscription_id)

    async def get_all_subscription(self, query_dict: Optional[dict] = None) -> List:
        if query_dict is None:
            query_dict = {}
        return await self.repository.list_subscriptions(**query_dict or {})
