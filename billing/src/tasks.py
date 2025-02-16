import asyncio
import json
import time
import logging
from datetime import datetime, timedelta, UTC, timezone

from aiohttp import ClientResponseError
from aiohttp.log import access_logger
from celery.bin.result import result
from fastapi import HTTPException

import httpx

from celery import Celery
from sqlalchemy.util import await_only
from starlette import status
from concurrent.futures import Future

from billing.src.api.dependencies import get_current_user
from billing.src.models.payments import PaymentModel, PaymentStatus
from billing.src.models.tariffs import TariffModel

from payments.providers.yookassa_provider import YooKassaProvider

from billing.src.db.postgres import get_sync_session, async_session
from billing.src.core.config import settings

logger = logging.getLogger(__name__)

celery = Celery(
    __name__,
    broker=settings.celery_broker_url,
    backend=settings.celery_broker_url,
)

provider = YooKassaProvider(
    account_id='1023840',
    secret_key='test_xB8klULgAEuzogIqiJmKvdKLI5-9SOOTBxFYI6zOjZM',
)

async def get_auth_token():
    async with httpx.AsyncClient() as client:
        # Попытка авторизоваться
        auth_data = {
            "password": settings.billing_password,
            "username": settings.billing_username,
        }

        try:
            auth_response = await client.post(
                'http://auth_api:8000/api/v1/auth/login',
                json=auth_data,
            )
            auth_response.raise_for_status()
            return json.loads(auth_response.text)['access_token']

        except httpx.HTTPError as e:
            if e.response.status_code == 401:
                logging.warning(
                    "Неверные учетные данные. Попробуем зарегистрировать нового пользователя.")

                # Данные для регистрации нового пользователя
                register_data = {
                    "email": "test1@example.com",
                    "is_superuser": True,
                    "password": settings.billing_password,
                    "username": settings.billing_username
                }

                try:
                    register_response = await client.post(
                        'http://auth_api:8000/api/v1/auth/register',
                        json=register_data,
                        timeout = 2
                    )
                    register_response.raise_for_status()
                    logging.info("Новый пользователь зарегистрирован.")

                    # После успешной регистрации снова попытаемся войти
                    auth_response = await client.post(
                        'http://auth_api:8000/api/v1/auth/login',
                        json=auth_data,
                        timeout=2
                    )
                    auth_response.raise_for_status()
                    return json.loads(auth_response.text)['access_token']

                except httpx.HTTPError as ex:
                    logging.error(f"Произошла ошибка при регистрации: {ex}")
                    raise ex

            else:
                logging.error(
                    f"Произошла неожиданная ошибка при авторизации: {e}")
                raise e

async def subscript_process(payment, tariff, response_text):
    """
    Функция для обработки подписки и отправки данных на API.

    :param payment: Объект платежа.
    :param tariff: Объект тарифа.
    :param response_text: Ответный текст.
    :return: None
    """
    # Получаем текущую дату и время в UTC
    now_utc_datetime = datetime.now(tz=timezone.utc)
    end_date = now_utc_datetime + timedelta(days=tariff.duration)

    # Формируем данные для отправки
    data = {
        'user_id': str(payment.user_id),
        'plan_type': tariff.name,
        'start_date': now_utc_datetime.isoformat(),
        'end_date': end_date.isoformat(),
        'price': float(tariff.price),
        'status': 'active',
    }
    print(data)
    # Отправляем POST-запрос на subscriptions_api
    access_token = await get_auth_token()
    async with httpx.AsyncClient() as client:
        try:
             # Формирование заголовков с токеном аутентификации
            headers = {"Authorization": f"Bearer {access_token}"}

            # Отправка POST-запроса
            response = await client.post(
                "http://subscriptions_api:8000/api/subscriptions/api/v1/subscription/",
                json=data,
                headers=headers
            )

            logger.info(
                f"Subscriptions API response status: {response.status_code}")
            logger.info(f"Subscriptions API response body: {response.text}")

        except HTTPException as e:
            # Обрабатываем исключение и возвращаем понятное сообщение
            message = f"Subscription creation failed: {e.detail}"
            logger.error(message)
            raise Exception(message)

        except httpx.RequestError as e:
            logger.error(f"Request to subscriptions API failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Subscriptions API is unavailable"
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
                payment.status = new_payment_data.get('status')
                response_text = subscript_process(payment, tariff,
                                                  response_text)
                session.add(payment)

            elif new_payment_data.get('status') == repr(PaymentStatus.WAITING_FOR_CAPTURE):
                new_payment_data = provider.capture_payment(
                    payment_id=new_payment_data.get('id')
                )
                loop = asyncio.get_event_loop()
                response_text = loop.run_until_complete(
                    subscript_process(payment, tariff, response_text)
                )
                payment.status = new_payment_data.get('status')
                session.add(payment)


            session.commit()
            return response_text

        tries += 1
        delay_in_seconds += delay_in_seconds
