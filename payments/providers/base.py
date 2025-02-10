# Абстрактный класс провайдера платежей

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from uuid import UUID


class BasePaymentProvider(ABC):
    @abstractmethod
    def create_payment(
        self,
        amount: float,
        currency: str,
        description: str,
        metadata: Optional[Dict] = None,
        idempotence_key: Optional[UUID] = None
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def capture_payment(
        self,
        payment_id: str,
        idempotence_key: Optional[UUID] = None
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def handle_webhook(self, event: str, data: Dict) -> None:
        pass

    @abstractmethod
    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        pass
