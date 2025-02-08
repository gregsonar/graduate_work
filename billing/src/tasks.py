import time
import logging
from datetime import datetime, timedelta, UTC
from http.client import HTTPException

import httpx

from celery import Celery
from starlette import status

from billing.src.models.payments import PaymentModel, PaymentStatus
from billing.src.models.tariffs import TariffModel

from payments.providers.yookassa_provider import YooKassaProvider

from db.postgres import get_sync_session
from core.config import settings


celery = Celery(__name__)
celery.conf.broker_url = settings.celery.broker_url
celery.conf.result_backend = settings.celery.broker_url

provider=YooKassaProvider(
    account_id=settings.yookassa_shopid,
    secret_key=settings.yookassa_token,
)

def subscript_process(payment, tariff, response_text):
    with httpx.Client() as client:

        now_utc_datetime = datetime.now(UTC)

        try:
            data = {
                'user_id': payment.user_id,
                'plan_type': tariff.name,
                'start_date': now_utc_datetime,
                'end_date': now_utc_datetime + timedelta(tariff.duration),
                'price': tariff.price,
            }
            response = client.post(url=settings.SUBSCRIPTIONS_URL, data=data)

            try:
                subscription_data = response.json()
                response_text = response_text + f"New subscribe {subscription_data.id} for user {payment.user_id}."
                return response_text

            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Invalid response from subscriptions service",
                )

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Subscriptions service is unavailable"
            )


@celery.task(name="Check payment status & subscribe")
def subscribe(payment_model_id, payment_id, payment_status):
    tries = 1
    delay_in_seconds = settings.check_delay_in_seconds

    while True:
        time.sleep(delay_in_seconds)
        logging.info(f'Try #{tries}')

        new_payment_data = provider.get_payment(payment_id)

        if new_payment_data.get('status') != payment_status:

            session = get_sync_session()
            payment = session.get(PaymentModel, payment_model_id)
            tariff = session.get(TariffModel, payment.tariff_id)

            response_text = f"Payment {payment.payment_id} changed the status."

            if new_payment_data.get('status') == repr(PaymentStatus.SUCCEEDED):

                response_text = subscript_process(payment, tariff, response_text)

                payment.status = new_payment_data.get('status')
                session.add(payment)

            elif new_payment_data.get('status') == repr(PaymentStatus.WAITING_FOR_CAPTURE):
                new_payment_data = provider.capture_payment(payment_id=payment.payment_id)

                payment.status = new_payment_data.get('status')
                session.add(payment)

            session.commit()
            return response_text

        tries += 1
        delay_in_seconds += delay_in_seconds
