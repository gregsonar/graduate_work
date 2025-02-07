import time
import logging
from datetime import datetime, timedelta
import httpx

from celery import Celery
from sqlalchemy import select
from yookassa import Payment, Configuration

from billing.src.models.payments import PaymentModel, PaymentStatus
from billing.src.models.tariffs import TariffModel

from payments.providers.yookassa_provider import YooKassaProvider
# from models.subscription import SubscriptionModel, SubscriptionStatus

from db.postgres import get_sync_session
from core.config import settings
# from services.auth_service import auth_subscribe, auth_unsubscribe

celery = Celery(__name__)
celery.conf.broker_url = settings.celery.broker_url
celery.conf.result_backend = settings.celery.broker_url

provider=YooKassaProvider(
    account_id=settings.yookassa_shopid,
    secret_key=settings.yookassa_token,
)

@celery.task(name="Check payment status & subscribe")
def subscribe(payment_model_id, payment_id, payment_status):
    Configuration.configure(
        account_id=settings.yookassa_shopid,
        secret_key=settings.yookassa_token
    )
    tries = 1
    delay_in_seconds = settings.check_delay_in_seconds
    while True:
        time.sleep(delay_in_seconds)
        logging.info(f'Try #{tries}')
        new_payment_data = provider.get_payment(payment_id)
        # new_payment_data = Payment.find_one(str(payment_id))
        if new_payment_data.get('status') != payment_status:
            session = get_sync_session()
            payment = session.get(PaymentModel, payment_model_id)
            payment.status = new_payment_data.get('status')
            session.add(payment)
            response_text = f"Payment {payment.payment_id} changed the status."
            if new_payment_data.get('status') == repr(PaymentStatus.SUCCEEDED):
                tariff = session.get(TariffModel, payment.tariff_id)
                # нужна возможность получать подписки по шв пользователя
                # query = session.execute(
                #     select(SubscriptionModel).
                #     where(SubscriptionModel.user_id == payment.user_id)
                # )
                # subscription = query.scalars().first()
                # проверяем была ли подписка до этого
                if not subscription:
                    with httpx.Client() as client:
                        try:
                            data = {
                                'user_id': payment.user_id,
                                'plan_type': tariff.name,
                                'start_date': ,
                                'end_date': ,
                                'price': tariff.price,

                            }
                            response = client.post(
                                url=settings.SUBSCRIPTIONS_URL, data=payment.user_id)
        #             subscription = SubscriptionModel(
        #                 user_id=payment.user_id,
        #                 tariff_id=payment.tariff_id,
        #                 start_date=datetime.now(),
        #                 end_date=datetime.now() + timedelta(days=tariff.duration),
        #                 status=repr(SubscriptionStatus.ACTIVE),
        #                 payment_id=payment.id
        #             )
        #             session.add(subscription)
        #         else:
        #             subscription.tariff_id = payment.tariff_id
        #             subscription.start_date = datetime.now()
        #             subscription.end_date = datetime.now() + timedelta(days=tariff.duration)
        #             subscription.status = repr(SubscriptionStatus.ACTIVE)
        #             subscription.payment_id = payment.id
        #
        #         response_text += f"New subscribe {subscription.id} for user {payment.user_id}."
        #     session.commit()
        #     auth_subscribe(payment.user_id, payment.tariff_id)
        #     return response_text
        # tries += 1
        # delay_in_seconds += delay_in_seconds