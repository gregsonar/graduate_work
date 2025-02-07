from uuid import UUID

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
        YooKassaProvider(
            account_id=settings.yookassa_shopid,
            secret_key=settings.yookassa_token,
        )
        self.db_session = db_session

    async def save_payment_in_db(
            self,
            user_id: UUID,
            tariff: TariffModel,
            payment: YooKassaProvider.create_payment,
    )  -> PaymentModel:
        """Метод для сохранения платежа в базе."""
        new_db_payment = PaymentModel(
            user_id=user_id,
            tariff_id=tariff.id,
            status=payment.status,
            payment_method_id=payment.payment_method.id,
            payment_id=payment.id,
        )
        self.db_session.add(new_db_payment)
        await self.db_session.commit()
        return new_db_payment

    async def save_refund_in_bd(
            self,
            refund: YooKassaProvider.create_refund,
    ) -> None:
        """Метод для сохранения возврата в базе."""
        # В нашем модуле юкассы метод отсутствует.
        refund_db = RefundModel(
            payment_id=refund.payment_id,
            refund_id=refund.id,
            status=refund.status,
            amount=refund.amount.value
        )
        self.db_session.add(refund_db)
        await self.db_session.commit()

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

    async def create_payment(self, user_id: UUID, tariff_id: UUID) -> str:

        # if await self.is_subscribed(user_id):
        #     raise AlreadySubscribedError

        tariff = await self.db_session.get(TariffModel, tariff_id)
        if not tariff:
            raise TariffNotFoundError

        payment = YooKassaProvider.create_payment(
            amount=tariff.price,
            currency=tariff.currency,
            description=tariff.description,
        )
        payment_db = await self.save_payment_in_db(user_id, tariff, payment)
        subscribe.delay(payment_db.id, payment.id, payment.status)

        return CreatedPaymentSchema(
            redirect_url=payment.confirmation.return_url
        )



#     async def is_subscribed(self, user_id) -> bool:
#         # Не нашел возможности проверить наличие подписки по шв пользователя
#         # if subscription:
#         #     return True
#         # return False
#

#     async def unsubscribe(self, user_id: UUID, return_funds: bool) -> None:
#         # Переписать с учетом сервиса подписок и модуля платежей
#         subscription = await self.get_user_subscription(user_id)
#
#         if return_funds:
#             tariff = await self.session.get(TariffModel, subscription.tariff_id)
#             payment_db = await self.session.get(PaymentModel, subscription.payment_id)
#             payload = self.get_refund_payload(payment_db.payment_id, tariff.price, tariff.currency)
#
#             refund = Refund.create(payload)
#             await self.save_refund(refund)
#
#             if refund.status != self.SUCCEEDED:
#                 raise RefundError
#
#         subscription.status = str(SubscriptionStatus.CANCELED)
#         await self.session.commit()
#         await auth_async_unsubscribe(user_id=user_id)
#



def get_billing_service(
        session: AsyncSession = Depends(get_session)
):
    return BillingService(session)