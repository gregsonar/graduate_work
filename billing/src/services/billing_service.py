from typing import Dict
from uuid import UUID

import httpx
from billing.src.core.config import settings
from billing.src.core.exceptions import TariffNotFoundError
from billing.src.db.postgres import get_session
from billing.src.models.payments import PaymentModel

# from billing.src.models.refunds import RefundModel
from billing.src.models.tariffs import TariffModel
from billing.src.schemas.payment_schemas import CreatedPaymentSchema
from billing.src.schemas.tariff_schemas import PaymentSchema
from billing.src.tasks import subscribe
from fastapi import Depends, HTTPException, status
from payments.providers.yookassa_provider import YooKassaProvider
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BillingService:

    def __init__(self, db_session: AsyncSession):
        self.yoo_provider = YooKassaProvider(
            account_id=settings.yookassa_shopid,
            secret_key=settings.yookassa_token,
        )
        self.db_session = db_session
        self.client = httpx.AsyncClient()
        self.base_url = settings.base_url

    async def save_payment_in_db(
        self,
        user_id: UUID,
        tariff: TariffModel,
        payment: Dict[str, str],
    ) -> PaymentModel:
        """Метод для сохранения платежа в базе."""
        print(user_id)
        new_db_payment = PaymentModel(
            user_id=user_id,
            tariff_id=tariff,
            status=payment.get("status"),
            payment_id=payment.get("id"),
        )
        self.db_session.add(new_db_payment)
        await self.db_session.commit()
        return new_db_payment

    # async def save_refund_in_bd(
    #         self,
    #         refund: YooKassaProvider.create_refund,
    # ) -> None:
    #     """Метод для сохранения возврата в базе."""
    #     # В нашем модуле юкассы метод отсутствует.
    #     refund_db = RefundModel(
    #         payment_id=refund.payment_id,
    #         refund_id=refund.id,
    #         status=refund.status,
    #         amount=refund.amount.value
    #     )
    #     self.db_session.add(refund_db)
    #     await self.db_session.commit()

    async def get_all_payments(self, user_id) -> list[PaymentSchema]:
        """Метод для получения из БД всех платежей пользователя."""
        query = await self.db_session.execute(
            select(PaymentModel).where(PaymentModel.user_id == user_id)
        )
        payments = []
        for payment in query.scalars().all():
            payments.append(
                PaymentSchema(
                    id=payment.id,
                    user_id=payment.user_id,
                    tariff_id=payment.tariff_id,
                    status=payment.status,
                )
            )
        return payments

    async def create_payment(
        self, user_id: UUID, tariff_id: UUID
    ) -> CreatedPaymentSchema:

        tariff = await self.db_session.get(TariffModel, tariff_id)
        if not tariff:
            raise TariffNotFoundError

        payment = self.yoo_provider.create_payment(
            amount=tariff.price,
            currency=tariff.currency,
            description=tariff.description,
        )

        payment_db = await self.save_payment_in_db(user_id, tariff.id, payment)
        await subscribe.delay(payment_db.id, payment.get("id"), payment.get("status"))

        return CreatedPaymentSchema(
            redirect_url=payment.get("confirmation").get("confirmation_url")
        )

    async def cancel_subscription(
        self,
        user_id: UUID,
        refund: bool,
        reason: str,
        immediate: bool,
    ):
        try:
            # Получаем информацию о подписке
            response = await self._get_subscription(user_id)
            subscription_id = response.json()["id"]

            # Определяем данные для отмены подписки
            data = {"reason": reason, "immediate": immediate}

            await self._cancel_subscription(
                subscription_id,
                data,
            )

            if refund:
                # Логика возврата средств
                pass

        except (KeyError, ValueError, httpx.HTTPError) as e:
            if isinstance(e, KeyError) or isinstance(e, ValueError):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="The subscription not found",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e),
                )

    async def _get_subscription(
        self,
        user_id: UUID,
    ):
        url = self.base_url + f"user/{user_id}"
        response = await self.client.get(url)
        return response

    async def _cancel_subscription(self, subscription_id: UUID, data: dict):
        url = self.base_url + f"{subscription_id}/cancel"
        response = await self.client.post(url, json=data)
        return response


def get_billing_service(session: AsyncSession = Depends(get_session)):
    return BillingService(session)
