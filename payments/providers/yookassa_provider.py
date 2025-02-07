# реализация провайдера платежей для YooKassa

import json
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

import requests
from yookassa import Configuration, Payment

from payments.exceptions import PaymentCreationError, PaymentCaptureError, PaymentStatusError
from payments.schemas import YooKassaPaymentSchema, YooKassaRefundSchema


class YooKassaProvider:
    def __init__(self, account_id: str, secret_key: str):
        Configuration.configure(account_id, secret_key)

    @staticmethod
    def _generate_idempotence_key() -> str:
        return str(uuid4())

    def create_payment(
            self,
            amount: float,
            currency: str = "RUB",
            description: str = "",
            metadata: Optional[Dict] = None,
            capture: bool = False,
            idempotence_key: Optional[UUID] = None
    ) -> Dict[str, Any]:
        try:
            idempotence_key = idempotence_key or self._generate_idempotence_key()

            payment = Payment.create({
                "amount": {
                    "value": amount,
                    "currency": currency
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": "https://your-service.com/return"
                },
                "capture": capture,
                "description": description,
                "metadata": metadata or {}
            }, idempotence_key)

            # Преобразуем JSON-строку в словарь
            payment_data = json.loads(payment.json())
            return YooKassaPaymentSchema(**payment_data).model_dump()

        except Exception as e:
            raise PaymentCreationError(f"Payment creation failed: {str(e)}")

    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        try:
            payment = Payment.find_one(payment_id)

            # Преобразуем JSON-строку в словарь
            payment_data = json.loads(payment.json())
            return YooKassaPaymentSchema(**payment_data).dict()

        except Exception as e:
            raise PaymentStatusError(f"Failed to get payment status: {str(e)}")

    def capture_payment(
            self,
            payment_id: str,
            idempotence_key: Optional[UUID] = None
    ) -> Dict[str, Any]:
        try:
            idempotence_key = idempotence_key or self._generate_idempotence_key()

            payment = Payment.capture(
                payment_id,
                None,  # Полный захват суммы
                idempotence_key
            )

            # Преобразуем JSON-строку в словарь
            payment_data = json.loads(payment.json())
            return YooKassaPaymentSchema(**payment_data).model_dump()

        except PaymentCaptureError as e:
            raise PaymentCaptureError(f"Payment capture failed: {str(e)}")

    def handle_webhook(self, event: str, data: Dict) -> None:
        handlers = {
            'payment.succeeded': self._handle_payment_succeeded,
            'payment.canceled': self._handle_payment_canceled,
            'refund.succeeded': self._handle_refund_succeeded
        }

        handler = handlers.get(event)
        if handler:
            handler(data)

        # todo: add unhandled webhook type exception

    def _handle_payment_succeeded(self, data: Dict) -> None:
        # Логика обработки успешного платежа
        payment = YooKassaPaymentSchema(**data)
        print(f"Payment {payment.id} succeeded")

    def _handle_payment_canceled(self, data: Dict) -> None:
        # Логика обработки отмены
        payment = YooKassaPaymentSchema(**data)
        print(f"Payment {payment.id} canceled")

    def _handle_refund_succeeded(self, data: Dict) -> None:
        # Логика обработки возврата
        refund = YooKassaRefundSchema(**data)
        print(f"Refund {refund.id} succeeded")
