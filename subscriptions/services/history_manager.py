from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from subscriptions.services.interfaces import ISubscriptionHistoryManager
from subscriptions.models.subscription import SubscriptionHistory
from subscriptions.schemas.subscription_schema import SubscriptionHistoryResponse

class SubscriptionHistoryManager(ISubscriptionHistoryManager):
    def __init__(self, session: AsyncSession):
        self.session = session



    async def add_record(
        self,
        subscription_id: UUID,
        action: str,
        details: dict | None = None
    ) -> None:
        print(details)
        history_entry = SubscriptionHistory(
            subscription_id=subscription_id,
            action=action,
            details={key: str(value) for key, value  in details.items()} or {}
        )
        print(history_entry)
        self.session.add(history_entry)
        await self.session.commit()

    async def get_history(
        self,
        subscription_id: UUID
    ) -> list[SubscriptionHistoryResponse]:
        result = await self.session.execute(
            select(SubscriptionHistory)
            .filter(SubscriptionHistory.subscription_id == subscription_id)
            .order_by(SubscriptionHistory.created_at.desc())
        )
        history_entries = result.scalars().all()
        return [SubscriptionHistoryResponse.model_validate(entry) for entry in history_entries]