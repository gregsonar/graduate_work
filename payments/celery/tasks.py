# Фоновая задача для автоплатежей.
# Ретраи при неудачном списании.
# Логика обработки очереди.

import asyncio
import logging
import os
from datetime import UTC, datetime

import aiohttp
from celery import Celery
from dotenv import load_dotenv
from payments import db
from payments.models.payment_jobs import PaymentJob
from payments.providers.yookassa_provider import YooKassaProvider

# todo: Замечание: в этих задачах используется асинхронный запрос для получения подписок, а обработка платежей
# с записью в БД — выполняется синхронно (с вызовом db.session.add(payment) и т. д.).
# Нужно следить за тем, чтобы вызовы к базе данных выполнялись корректно в синхронном контексте или обернуть их
# через asyncio.run/async_to_sync, если потребуется.
# Возможно, для воркера целесообразно создать отдельное
# синхронное подключение к БД, если задачи остаются синхронными.

# Настройки Celery
celery = Celery("payments")
celery.conf.broker_url = "redis://localhost:6379/0"
# Используем встроенный планировщик Celery Beat
celery.conf.beat_schedule = {
    "schedule-autopayments-every-12-hours": {
        "task": "payments.celery.tasks.schedule_autopayments",
        "schedule": 12 * 60 * 60,  # каждые 12 часов
    },
    "run-task-a-every-10-seconds": {  # задачи только для отладки! -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        "task": "payments.celery.tasks.tasks.task_a",
        "schedule": 10.0,  # Каждые 10 секунд
    },
}

# Логирование
logger = logging.getLogger(__name__)

load_dotenv()

# Инициализация провайдера
provider = YooKassaProvider(
    account_id=os.getenv("YOOKASSA_SHOP_ID", "1234567"),
    secret_key=os.getenv("YOOKASSA_API_KEY", "test_apikey123"),
)

# URL API подписок
SUBSCRIPTIONS_API_URL = "http://subscriptions/api/v1/subscription/admin/due"


async def fetch_due_subscriptions():
    """Асинхронный запрос в API подписок"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(SUBSCRIPTIONS_API_URL, timeout=30) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(
                        f"Failed to fetch subscriptions, status: {response.status}"
                    )
                    return []
        except Exception as e:
            logger.error(f"Error fetching subscriptions: {e}")
            return []


@celery.task(bind=True, max_retries=3, default_retry_delay=60 * 5)
def process_autopayment(self, subscription):
    """Обрабатывает автоплатёж для подписки"""
    required_keys = ["id", "payment_method_id", "amount"]
    if not all(key in subscription for key in required_keys):
        logger.error("Subscription data is missing required keys")
        return

    try:
        subscription_id = subscription["id"]
        payment_method_id = subscription["payment_method_id"]
        amount = subscription["amount"]

        if not payment_method_id:
            logger.error(f"No saved payment method for subscription {subscription_id}")
            return

        # Создаём платёж через YooKassa
        payment_data = provider.make_recurrent_payment(
            amount=amount,
            currency="RUB",
            description=f"Autopayment for subscription {subscription_id}",
            payment_method_id=payment_method_id,
            capture=True,
        )

        # Записываем платёж в БД
        payment = PaymentJob(
            subscription_id=subscription_id,
            payment_id=payment_data["id"],
            status=payment_data["status"],
            created_at=datetime.now(UTC),
        )
        try:
            db.session.add(payment)
        finally:
            db.session.commit()

        logger.info(
            f"Autopayment {payment_data['id']} created for subscription {subscription_id}"
        )

        # Проверяем статус
        if payment_data["status"] == "succeeded":
            logger.info(f"Payment {payment_data['id']} succeeded")
        else:
            logger.warning(
                f"Payment {payment_data['id']} is in status {payment_data['status']}"
            )
            self.retry()

    except Exception as e:
        logger.error(
            f"Error processing autopayment for subscription {subscription_id}: {e}"
        )
        self.retry(exc=e)


@celery.task
def schedule_autopayments():
    """Запрашивает подписки и создаёт задачи на автоплатежи"""
    loop = asyncio.get_event_loop()
    subscriptions = loop.run_until_complete(fetch_due_subscriptions())

    for subscription in subscriptions:
        process_autopayment.delay(subscription)

    logger.info(f"Scheduled {len(subscriptions)} autopayments")


# Задачи для отладки -=-=-=-=-=-=-=-=-=-=-=--=-=-=-=-=-=-=-=-=-=-=-=--=-=-==-=-=-=--==-=-=-==-=-=-=-=-=-=-=-=-=-=--==-=-


@celery.task
def task_a():
    logger.info("Task A: Starting execution")
    # Ставим Task B в очередь с задержкой 2 секунды
    task_b.apply_async(countdown=2)
    return "Task A: Successfully queued Task B"


@celery.task
def task_b():
    logger.info("Task B: Executing and writing to log")
    print("Task B: This message goes to stdout")
    return "Task B: Completed successfully"
