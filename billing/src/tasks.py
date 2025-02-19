import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone

import httpx
from billing.src.core.config import settings
from billing.src.db.postgres import get_sync_session
from billing.src.models.payments import PaymentModel, PaymentStatus
from billing.src.models.tariffs import TariffModel
from celery import Celery
from celery.schedules import crontab
from payments.providers.yookassa_provider import YooKassaProvider

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


async def subscript_process(payment, tariff, response_text):
    async with httpx.AsyncClient() as client:
        try:
            # Получение информации о текущей подписке
            response = await get_subscription(client, payment.user_id)

            # Проверка статуса ответа
            if response.status_code == httpx.codes.NOT_FOUND:
                # Подписка отсутствует, создаем новую
                await create_subscription(client, payment, tariff)
            elif response.status_code == httpx.codes.OK:
                # Подписка существует, обновим её
                await update_subscription(client, response.json(), tariff)
            else:
                logger.warning(
                    f"Something went wrong with the subscription API. "
                    f"Status code: {response.status_code}"
                )

        except Exception as e:
            logger.exception(str(e))
            return {"error": str(e)}


async def get_subscription(client, user_id):
    return await client.get(settings.base_url + f"user/{user_id}")


async def create_subscription(client, payment, tariff):
    base_url = settings.base_url
    # Получаем текущую дату и время в UTC
    now_utc_datetime = datetime.now(timezone.utc)
    end_date = now_utc_datetime + timedelta(days=tariff.duration)

    # Данные для создания новой подписки
    data = {
        'user_id': str(payment.user_id),
        'plan_type': tariff.name,
        'start_date': now_utc_datetime.isoformat(),
        'end_date': end_date.isoformat(),
        'price': float(tariff.price),
    }

    # Создание новой подписки
    response = await client.post(base_url, json=data)

    if response.status_code == httpx.codes.CREATED:
        logger.info("Subscription created successfully")
    else:
        logger.error(
            f"Failed to create subscription. "
            f"Status code: {response.status_code}. "
            f"Response text: {response.text}"
        )


async def update_subscription(client, subscription_data, tariff):
    base_url = settings.base_url
    # Получаем текущую дату и время в UTC
    now_utc_datetime = datetime.now(timezone.utc)

    # Данные для обновления подписки
    data = {}

    # Обновление подписки в зависимости от статуса
    if subscription_data['status'] == 'expired':
        # Подписка истекла, возобновляем её
        data = {
            'status': 'active',
            'plan_type': tariff.name,
            'end_date': (
                now_utc_datetime + timedelta(days=tariff.duration)
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        log_message = "Expired subscription renewed successfully"
    elif subscription_data['status'] == 'pending':
        # Активируем подписку
        data = {'status': 'active'}
        log_message = "Subscription activated successfully"
    elif subscription_data['status'] == 'active':
        # Получаем текущую дату и время в UTC
        old_end_date = datetime.strptime(
            subscription_data['end_date'], "%Y-%m-%dT%H:%M:%SZ"
        )
        new_end_date = old_end_date + timedelta(days=tariff.duration)
        data = {
            'end_date': new_end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        # Проверка соответствия плана подписки текущему тарифу
        if subscription_data['plan_type'] != tariff.name:
            # План подписки отличается от нового тарифа, необходимо обновление
            # Данные для обновления подписки
            data['plan_type'] = tariff.name
            log_message = "Plan type and end date updated successfully"
        else:
            log_message = "Subscription updated successfully"

    # Обновление подписки
    response = await client.put(
        base_url + f"{subscription_data['id']}",
        json=data,
    )

    # Обработка ответа
    if response.status_code == httpx.codes.OK:
        logger.info(log_message)
    else:
        logger.error(
            f"Failed to update subscription. "
            f"Status code: {response.status_code}. "
            f"Response text: {response.text}")


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

            elif new_payment_data.get('status') == repr(
                    PaymentStatus.WAITING_FOR_CAPTURE
            ):
                new_payment_data = provider.capture_payment(
                    payment_id=new_payment_data.get('id')
                )
                loop = asyncio.get_event_loop()
                response_text = loop.run_until_complete(
                    subscript_process(payment, tariff, response_text)
                )
                payment.status = new_payment_data.get('status')
                response_text = loop.run_until_complete(
                    subscript_process(payment, tariff, response_text)
                )
                session.add(payment)

            session.commit()
            return response_text

        tries += 1
        delay_in_seconds += delay_in_seconds


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='0', hour='0'),
        check_subscriptions_expiration.s(),
    )


@celery.task()
def check_subscriptions_expiration():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_subscriptions_expiration_async())


async def check_subscriptions_expiration_async():
    async with httpx.AsyncClient() as client:
        try:
            # Получение списка всех активных подписок
            response = await client.get(settings.base_url + "admin/all")
            subscriptions = response.json()

            # Проверка каждой активной подписки на истечение срока
            for subscription in subscriptions:
                if subscription["status"] == "active":
                    await handle_active_subscription(client, subscription)

        except Exception as e:
            print(f"Ошибка при проверке подписок: {str(e)}")


async def handle_active_subscription(client, subscription):
    # Получение даты окончания подписки
    end_date = datetime.strptime(
        subscription["end_date"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
        tzinfo=timezone.utc)

    # Текущее время
    current_time = datetime.now(timezone.utc)

    # Проверка истечения срока подписки
    if current_time > end_date:
        # Подписка истекла, меняем статус на "expired"
        status_data = {"status": "expired"}
        response = await client.put(
            settings.base_url + f"{subscription['id']}",
            json=status_data,
        )

        if response.status_code == httpx.codes.OK:
            print(
                f"Подписка {subscription['id']} истекла "
                f"и статус успешно изменён."
            )
        else:
            print(f"Не удалось изменить статус подписки {subscription['id']}."
                  f"Код состояния: {response.status_code}. "
                  f"Ответ сервера: {response.text}"
                  )
