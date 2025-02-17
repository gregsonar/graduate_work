from datetime import datetime, timezone, timedelta
from typing import Dict
from uuid import UUID

import requests
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from billing.src.core.exceptions import TariffNotFoundError
from billing.src.db.postgres import get_session
from billing.src.models.payments import PaymentModel
from billing.src.models.refunds import RefundModel
from billing.src.models.tariffs import TariffModel
from billing.src.schemas.payment_schemas import CreatedPaymentSchema
from billing.src.schemas.tariff_schemas import PaymentSchema
from payments.providers.yookassa_provider import YooKassaProvider
from billing.src.core.config import settings
from billing.src.tasks import subscribe

class BillingService:

    SUCCEEDED = 'succeeded'

    def __init__(self, db_session: AsyncSession):
        self.yoo_provider = YooKassaProvider(
            account_id=settings.yookassa_shopid,
            secret_key=settings.yookassa_token,
        )
        self.db_session = db_session

    async def save_payment_in_db(
            self,
            user_id: UUID,
            tariff: TariffModel,
            payment: Dict[str, str],
    )  -> PaymentModel:
        """Метод для сохранения платежа в базе."""
        print(user_id)
        new_db_payment = PaymentModel(
            user_id=user_id,
            tariff_id=tariff,
            status=payment.get('status'),
            payment_id=payment.get('id'),
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
                    status=payment.status
                )
            )
        return payments

    async def create_subscription(self, user_id: UUID, tariff_id: UUID) -> dict[
        str, str]:
        tariff = await self.db_session.get(TariffModel, tariff_id)
        if not tariff:
            raise TariffNotFoundError

        now_utc_datetime = datetime.now(tz=timezone.utc)
        end_date = now_utc_datetime + timedelta(days=tariff.duration)

        # Формируем данные для отправки
        data = {
            'user_id': str(user_id),
            'plan_type': tariff.name,
            'start_date': now_utc_datetime.isoformat(),
            'end_date': end_date.isoformat(),
            'price': float(tariff.price),
        }
        try:
            response = requests.get(
                url = f"http://subscriptions_api:8000/api/subscriptions/api/v1/subscription/user/{user_id}",
            )
            if response.status_code == 200:
                return {"message": "Еhe subscription already exists"}
            elif response.status_code == 404:
                response = requests.post(
                    url="http://subscriptions_api:8000/api/subscriptions/api/v1/subscription/",
                    json=data,
                )

                if response.status_code == 200:
                    return {"message": "Subscription created successfully"}
            else:
                return {
                    "error": f"Something went wrong with the subscription API. Status code: {response.status_code}"
                }

        except Exception as e:
            return {"error": str(e)}

    async def create_payment(self, user_id: UUID, tariff_id: UUID) -> str:

        tariff = await self.db_session.get(TariffModel, tariff_id)
        if not tariff:
            raise TariffNotFoundError

        payment = self.yoo_provider.create_payment(
            amount=tariff.price,
            currency=tariff.currency,
            description=tariff.description,
        )

        payment_db = await self.save_payment_in_db(user_id, tariff.id, payment)
        subscribe.delay(payment_db.id, payment.get('id'), payment.get('status'))

        return CreatedPaymentSchema(
            redirect_url=payment.get('confirmation').get('confirmation_url')
        )

def get_billing_service(
        session: AsyncSession = Depends(get_session)
):
    return BillingService(session)