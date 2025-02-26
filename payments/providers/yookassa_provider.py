# реализация провайдера платежей для YooKassa

import json
import logging
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

import requests
from yookassa import Configuration, Payment

from payments.exceptions import (
    PaymentCaptureError,
    PaymentCreationError,
    PaymentStatusError
)
from payments.providers.base import BasePaymentProvider
from payments.schemas import YooKassaPaymentSchema, YooKassaRefundSchema

logger = logging.getLogger(__name__)


class YooKassaProvider(BasePaymentProvider):
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
            idempotence_key: Optional[UUID] = None,
            save_payment_method: Optional[bool] = False
    ) -> Dict[str, Any]:
        try:
            idempotence_key = idempotence_key or self._generate_idempotence_key()

            payment = self._create_payment_object(amount=amount,
                                                  currency=currency,
                                                  description=description,
                                                  metadata=metadata,
                                                  capture=capture,
                                                  save_payment_method=save_payment_method,
                                                  idempotence_key=idempotence_key)

            # Преобразуем JSON-строку в словарь
            payment_data = json.loads(payment.json())
            return YooKassaPaymentSchema(**payment_data).model_dump()

        except Exception as e:
            raise PaymentCreationError(f"Payment creation failed: {str(e)}")

    def make_recurrent_payment(
            self,
            amount: float,
            currency: str = "RUB",
            description: str = "",
            metadata: Optional[Dict] = None,
            capture: bool = False,
            payment_method_id: str = "",
            idempotence_key: Optional[UUID] = None
    ) -> Dict[str, Any]:
        try:
            idempotence_key = idempotence_key or self._generate_idempotence_key()

            payment = self._create_payment_object(amount=amount,
                                                  currency=currency,
                                                  description=description,
                                                  metadata=metadata,
                                                  capture=capture,
                                                  payment_method_id=payment_method_id,
                                                  idempotence_key=idempotence_key)

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
            return YooKassaPaymentSchema(**payment_data).model_dump()

        except Exception as e:
            raise PaymentStatusError(f"Failed to get payment status: {str(e)}")

    def cancel_payment(self,
            payment_id: str,
            idempotence_key: Optional[UUID] = None):
        try:
            payment_to_cancel = Payment.cancel(payment_id=payment_id,
                                               idempotency_key=idempotence_key)

            return payment_to_cancel
        except Exception as e:
            raise e

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

    def refund_payment(self,
                       payment_id: str,
                       idempotence_key: Optional[UUID] = None
    ) -> Dict[str, Any]:
        # Логика возвратов
        pass

    def handle_webhook(self, event: str, data: dict):
        handlers = {
            "payment.succeeded": self._handle_payment_succeeded,
            "payment.canceled": self._handle_payment_canceled,
            "payment.waiting_for_capture": self._handle_waiting_capture,
            "refund.succeeded": self._handle_refund_succeeded
        }

        if handler := handlers.get(event):
            handler(data)
            self.logger.info(f"Handled {event} for payment {data.get('id')}")
        else:
            self.logger.warning(f"Unhandled event type: {event}")

        # todo: add unhandled webhook type exception

    def _handle_payment_succeeded(self, data: dict):
        # Обновляем статус платежа в вашей системе
        payment_id = data["id"]
        self._update_payment_status(payment_id, "succeeded")

    def _handle_payment_canceled(self, data: dict):
        payment_id = data["id"]
        self._update_payment_status(payment_id, "canceled")

    def _handle_waiting_capture(self, data: dict):
        payment_id = data["id"]
        self._update_payment_status(payment_id, "waiting_for_capture")

    def _handle_refund_succeeded(self, data: dict):
        refund_id = data["id"]
        payment_id = data["payment_id"]
        self._process_refund(refund_id, payment_id)

    def _update_payment_status(self, payment_id: str, status: str):
        # логгирование информации о платеже
        print(f"Updating payment {payment_id} to status {status}")

    def _process_refund(self, refund_id: str, payment_id: str):
        # Логику обработки возврата
        print(f"Processing refund {refund_id} for payment {payment_id}")

    def _create_payment_object(
            self,
            amount: float,
            currency: str = "RUB",
            description: str = "",
            metadata: Optional[Dict] = None,
            capture: bool = False,
            payment_method_id: str = "",
            idempotence_key: Optional[UUID] = None,
            save_payment_method: Optional[bool] = False
    ):
        payment_data = {
            "amount": {
                "value": amount,
                "currency": currency
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://your-service.com/return"  # todo: добавить в .env
            },
            "save_payment_method": save_payment_method,  # Сохранение платежных данных для проведения автоплатежей
            "capture": capture,
            "description": description,
            "metadata": metadata or {}
        }
        if payment_method_id:
            payment_data.update({"payment_method_id": payment_method_id})
        return Payment.create(payment_data, idempotency_key=idempotence_key)
