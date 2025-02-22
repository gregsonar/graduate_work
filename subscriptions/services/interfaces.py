from abc import ABC, abstractmethod
from uuid import UUID
from typing import List, Optional

from subscriptions.models import SubscriptionStatus, Subscription
from subscriptions.schemas.subscription_schema import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    SubscriptionHistoryResponse,
)


class ISubscriptionRepository(ABC):
    @abstractmethod
    async def create(self, subscription_data: dict) -> SubscriptionResponse:
        pass

    @abstractmethod
    async def get(self, subscription_id: UUID) -> SubscriptionResponse:
        pass

    @abstractmethod
    async def get_with_user_id(self, user_id: UUID) -> SubscriptionResponse:
        pass

    @abstractmethod
    async def update(self, subscription_id: UUID, data: dict) -> SubscriptionResponse:
        pass

    @abstractmethod
    async def list_subscriptions(
        self,
        offset: int = 0,
        limit: int = 50,
        user_id: Optional[UUID] = None,
        status: Optional[SubscriptionStatus] = None,
        plan_type: Optional[str] = None,
    ) -> List[Subscription]:
        pass


class ISubscriptionStatusManager(ABC):
    @abstractmethod
    async def suspend(self, subscription_id: UUID, reason: str) -> None:
        pass

    @abstractmethod
    async def resume(self, subscription_id: UUID, comment: str | None) -> None:
        pass

    @abstractmethod
    async def cancel(self, subscription_id: UUID, reason: str, immediate: bool) -> None:
        pass


class ISubscriptionHistoryManager(ABC):
    @abstractmethod
    async def add_record(
        self, subscription_id: UUID, action: str, details: dict | None = None
    ) -> None:
        pass

    @abstractmethod
    async def get_history(
        self, subscription_id: UUID
    ) -> List[SubscriptionHistoryResponse]:
        pass


class ISubscriptionValidator(ABC):
    @abstractmethod
    async def validate_status_transition(
        self, current_status: str, new_status: str
    ) -> bool:
        pass

    @abstractmethod
    async def validate_dates(self, start_date: str, end_date: str) -> bool:
        pass
