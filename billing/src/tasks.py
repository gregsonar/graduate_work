import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import aiohttp
import httpx
from celery import Celery
from celery.schedules import crontab
from sqlalchemy.orm import Session

from billing.src.core.config import settings
from billing.src.db.postgres import get_sync_session
from billing.src.models.payments import PaymentModel, PaymentStatus
from billing.src.models.tariffs import TariffModel
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


class SubscriptionManager:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def get_subscription(self, user_id: str) -> httpx.Response:
        """Fetch subscription information for a user."""
        return await self._client.get(f"{self.base_url}user/{user_id}")

    async def subscript_process(self, payment: PaymentModel, tariff: TariffModel) -> Optional[str]:
        """Process subscription creation or update."""
        try:
            response = await self.get_subscription(payment.user_id)

            if response.status_code == httpx.codes.NOT_FOUND:

                return await self.create_subscription(payment, tariff)
            elif response.status_code == httpx.codes.OK:
                await self.update_subscription(response.json(), tariff)

                return response.json()['id']
            else:
                logger.warning(
                    f"Subscription API error. Status code: {response.status_code}"
                )
                return None

        except Exception as e:
            logger.exception(str(e))
            return None

    async def create_subscription(self, payment: PaymentModel, tariff: TariffModel) -> str:
        """Create a new subscription for a user."""
        now_utc = datetime.now(timezone.utc)
        end_date = now_utc + timedelta(days=tariff.duration)

        data = {
            "user_id": str(payment.user_id),
            "plan_type": tariff.name,
            "start_date": now_utc.isoformat(),
            "end_date": end_date.isoformat(),
            "price": float(tariff.price),
            "plan_id": str(tariff.id)
        }

        response = await self._client.post(self.base_url, json=data)

        if response.status_code == httpx.codes.CREATED:
            logger.info("Subscription created successfully")
            return response.json()["id"]

        logger.error(
            f"Failed to create subscription. Status: {response.status_code}. Response: {response.text}"
        )
        raise ValueError(f"Failed to create subscription: {response.text}")

    async def update_subscription(
            self,
            subscription_data: Dict[str, Any],
            tariff: TariffModel
    ) -> str:
        """Update an existing subscription."""
        now_utc = datetime.now(timezone.utc)

        data = self._prepare_subscription_update_data(
            subscription_data,
            tariff,
            now_utc
        )

        response = await self._client.put(
            f"{self.base_url}{subscription_data['id']}",
            json=data
        )

        if response.status_code == httpx.codes.OK:
            logger.info(f"Subscription {subscription_data['id']} updated successfully")
            return subscription_data["id"]

        logger.error(
            f"Failed to update subscription. Status: {response.status_code}. Response: {response.text}"
        )
        raise ValueError(f"Failed to update subscription: {response.text}")

    @staticmethod
    def _prepare_subscription_update_data(
            subscription_data: Dict[str, Any],
            tariff: TariffModel,
            now_utc: datetime
    ) -> Dict[str, Any]:
        """Prepare data for subscription update based on current status."""
        if subscription_data["status"] == "expired":
            return {
                "status": "active",
                "plan_type": tariff.name,
                "plan_id": str(tariff.id),
                "end_date": (now_utc + timedelta(days=tariff.duration)).isoformat()
            }

        if subscription_data["status"] == "pending":
            return {"status": "active"}

        old_end_date = datetime.fromisoformat(
            subscription_data["end_date"].replace("Z", "+00:00")
        )
        new_end_date = old_end_date + timedelta(days=tariff.duration)

        data = {"end_date": new_end_date.isoformat()}

        if subscription_data["plan_type"] != tariff.name:
            data["plan_type"] = tariff.name

        return data

    async def check_subscriptions_expiration(self) -> None:
        """Check and update expired subscriptions."""
        try:
            response = await self._client.get(f"{self.base_url}admin/all")
            subscriptions = response.json()

            for subscription in subscriptions:
                if subscription["status"] == "active":
                    await self._handle_active_subscription(subscription)

        except Exception as e:
            logger.error(f"Error checking subscriptions: {str(e)}")

    async def _handle_active_subscription(self, subscription: Dict[str, Any]) -> None:
        """Handle active subscription expiration check."""
        end_date = datetime.fromisoformat(
            subscription["end_date"].replace("Z", "+00:00")
        )
        current_time = datetime.now(timezone.utc)

        if current_time > end_date:
            status_data = {"status": "expired"}
            response = await self._client.put(
                f"{self.base_url}{subscription['id']}",
                json=status_data,
            )

            if response.status_code == httpx.codes.OK:
                logger.info(f"Subscription {subscription['id']} marked as expired")
            else:
                logger.error(
                    f"Failed to update subscription {subscription['id']} status. "
                    f"Status: {response.status_code}. Response: {response.text}"
                )


class AutoPaymentManager:
    def __init__(self, payment_provider: YooKassaProvider, session_factory):
        self.provider = payment_provider
        self.session_factory = session_factory

    async def fetch_due_subscriptions(self) -> List[Dict[str, Any]]:
        """Fetch subscriptions due for autopayment."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                        f"{settings.base_url}admin/due",
                        timeout=30
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    logger.error(f"Failed to fetch subscriptions, status: {response.status}")
                    return []
            except Exception as e:
                logger.error(f"Error fetching subscriptions: {e}")
                return []

    def process_single_payment(self, subscription: Dict[str, Any], payment_id: Optional[str] = None) -> str:
        """Process a single autopayment for a subscription."""
        logger.info(f"Starting process_single_payment for subscription {subscription['id']}")
        logger.info(f"Initial payment_id: {payment_id}")

        required_keys = ["id", "price", "user_id", "plan_id"]
        if not all(key in subscription for key in required_keys):
            logger.error(f"Subscription {subscription.get('id')} missing required keys")
            raise ValueError("Missing required subscription data")

        try:
            if payment_id:
                logger.info(f"Checking existing payment with ID: {payment_id}")
                payment_data = self.provider.get_payment(str(payment_id))
                if not payment_data:
                    logger.error(f"Payment {payment_id} not found in YooKassa")
                    raise ValueError(f"Payment {payment_id} not found")
            else:
                logger.info("Creating new payment...")
                payment_data = self._create_payment(subscription)
                logger.info(f"New payment created with ID: {payment_data.get('id')}")
                self._save_payment_to_db(payment_data, subscription)

            logger.info(f"[process_single_payment] Payment data received: {payment_data}")

            if payment_data["status"] == "succeeded":
                logger.info(f"Payment {payment_data['id']} succeeded")

                subscribe.delay(payment_data["id"], payment_data["status"])
                return payment_data["id"]

            elif payment_data["status"] == "waiting_for_capture":
                self.provider.capture_payment(payment_data["id"])

                logger.info(f"Payment {payment_data['id']} was captured successfully")

                self._update_payment_status(payment_data["id"], "succeeded")
                return payment_data["id"]

            elif payment_data["status"] == "pending":
                logger.info(f"Payment {payment_data['id']} is pending")  # вот тут обрывается логика работы с платежом
                raise ValueError("Payment not completed: pending")
                # return payment_data["id"]

            else:
                logger.error(
                    f"Payment {payment_data['id']} has unexpected status: {payment_data['status']}"
                )
                raise ValueError(f"Payment failed: {payment_data['status']}")

        except ValueError as e:
            logger.warning(f"Payment processing warning: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}", exc_info=True)
            raise

    def _create_payment(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Create a payment through the payment provider."""
        logger.info(f"Creating payment for subscription: {subscription['id']}")
        payment_data = self.provider.create_payment(
            amount=subscription["price"],
            currency="RUB",
            description=f"Autopayment for subscription {subscription['id']}",
            save_payment_method=True
        )
        logger.info(f"Payment created in YooKassa: {payment_data.get('id')}")
        return payment_data

    def _save_payment_to_db(
            self,
            payment_data: Dict[str, Any],
            subscription: Dict[str, Any]
    ) -> None:
        """Save payment information to database."""
        payment = PaymentModel(
            user_id=subscription["user_id"],
            tariff_id=subscription["plan_id"],
            status=payment_data["status"],
            payment_id=payment_data["id"],
            subscription_id=subscription["id"],
        )
        if "payment_method" in payment_data.keys():  # Сохраняем метод оплаты, если он есть (payment_method)
            method_id = payment_data["payment_method"]["id"]
            payment.method_id = method_id

        with self.session_factory() as session:
            try:
                session.add(payment)
                session.commit()
                logger.info(
                    f"Payment {payment_data['id']} saved for subscription {subscription['id']}"
                )
            except Exception as e:
                session.rollback()
                logger.error(f"Error saving payment to DB: {e}")
                raise

    def _update_payment_status(self, payment_id: str, status: str) -> None:
        """Update payment status in database."""
        with self.session_factory() as session:
            try:
                payment = session.query(PaymentModel).filter(
                    PaymentModel.payment_id == payment_id
                ).first()
                if payment:
                    payment.status = status
                    session.commit()

                    logger.info(f"Payment {payment_id} status updated to {status}")
            except Exception as e:
                session.rollback()
                logger.error(f"Error updating payment status: {e}")
                raise


@celery.task(name="Check payment status & subscribe")
def subscribe(payment_id: str, payment_status: str) -> None:
    """Handle subscription process after payment."""
    logger.info(f"Starting subscribe task for payment {payment_id} with status {payment_status}")

    async def _async_subscribe():
        session = get_sync_session()
        try:
            payment = session.query(PaymentModel).filter(
                PaymentModel.payment_id == payment_id
            ).first()

            if not payment:
                logger.error(f"Payment {payment_id} not found in database")
                return

            tariff = session.get(TariffModel, payment.tariff_id)

            if payment_status == "succeeded":
                async with SubscriptionManager(settings.base_url) as subscription_manager:
                    await subscription_manager.subscript_process(payment, tariff)
                    logger.info(f"Subscription processed for payment {payment_id}")

            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"Error in subscribe task: {e}", exc_info=True)
            raise
        finally:
            session.close()

    asyncio.run(_async_subscribe())


@celery.task()
def check_subscriptions_expiration():
    """Check and process expired subscriptions."""

    async def _run_check():
        async with SubscriptionManager(settings.base_url) as manager:
            await manager.check_subscriptions_expiration()

    asyncio.run(_run_check())


@celery.task(bind=True, max_retries=20, default_retry_delay=30)
def process_autopayment(self, subscription: Dict[str, Any], payment_id: Optional[str] = None) -> None:
    """Process autopayment for a subscription."""
    logger.info(f"Starting process_autopayment task for subscription {subscription['id']}")
    logger.info(f"Input payment_id: {payment_id}")

    payment_manager = AutoPaymentManager(provider, get_sync_session)

    try:
        if not payment_id:

            with payment_manager.session_factory() as session:
                logger.info("Checking recent payments in DB")
                recent_payment = session.query(PaymentModel).filter(
                    PaymentModel.subscription_id == subscription['id']
                ).order_by(PaymentModel.created.desc()).first()
                if recent_payment:
                    logger.info(f"Found recent payment in DB: {recent_payment.payment_id}")
                    payment_id = recent_payment.payment_id
                else:
                    logger.info("No recent payments found in DB")
        processed_payment_id = payment_manager.process_single_payment(subscription, payment_id)
        logger.info(f"Payment processed successfully. processed_payment_id: {processed_payment_id}")
        return processed_payment_id

    except ValueError as e:
        if "not completed" in str(e):
            logger.info(f"Payment not completed, retrying in {self.default_retry_delay} seconds")
            self.retry(exc=e, countdown=self.default_retry_delay)
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        self.retry(exc=e)


@celery.task
def schedule_autopayments() -> None:
   """Schedule autopayments for due subscriptions."""
   payment_manager = AutoPaymentManager(provider, get_sync_session)

   # Получаем активные задачи
   active_tasks = celery.control.inspect().active()
   if active_tasks is None:
       active_tasks = {}

   # Собираем subscription_ids из активных задач
   active_subscription_ids = set()
   for worker_tasks in active_tasks.values():
       for task in worker_tasks:
           if task['name'] == 'tasks.process_autopayment':
               try:
                   subscription_id = task['kwargs'].get('subscription', {}).get('id')
                   if subscription_id:
                       active_subscription_ids.add(subscription_id)
               except (KeyError, AttributeError):
                   continue

   # Получаем подписки для оплаты
   subscriptions = asyncio.run(payment_manager.fetch_due_subscriptions())

   scheduled_count = 0
   for subscription in subscriptions:
       # Проверяем, нет ли уже активной задачи для этой подписки
       if subscription['id'] not in active_subscription_ids:
           # Проверяем, нет ли недавних платежей в БД
           with payment_manager.session_factory() as session:
               recent_payment = session.query(PaymentModel).filter(
                   PaymentModel.subscription_id == subscription['id']
                   # ,
                   # PaymentModel.created >= datetime.now(timezone.utc) - timedelta(minutes=5)
               ).first()

               if not recent_payment:
                   process_autopayment.delay(subscription)
                   scheduled_count += 1

   if scheduled_count > 0:
       logger.info(f"Scheduled {scheduled_count} new autopayments")
   else:
       logger.debug("No new autopayments needed")


# Configure periodic tasks
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
   sender.add_periodic_task(
       crontab(minute='0', hour='0'),
       check_subscriptions_expiration.s(),
   )
   sender.add_periodic_task(
       crontab(minute='*/1'),
       schedule_autopayments.s(),
   )


@celery.task(bind=True, max_retries=5)
def check_payment_status(payment_id: str, subscription_id: str):
    """
    (не используется)
    Проверяет статус платежа и обрабатывает его соответственно.

    Args:
        payment_id: ID платежа в системе
        subscription_id: ID подписки пользователя
    """
    try:
        session = get_sync_session()

        # billing_service = BillingService(session)

        # Получаем текущий статус платежа
        payment_status = provider.get_payment(payment_id)

        if payment_status == PaymentStatus.WAITING_FOR_CAPTURE.value:
            # Захватываем платеж
            try:
                provider.capture_payment(payment_id)

                # Обновляем дату окончания подписки
                with SubscriptionManager(settings.base_url) as subscription_manager:

                    subscription_manager.update_subscription(
                        subscription_data=subscription_manager.get_subscription(subscription_id),
                    )
                    # subscript_process(payment, tariff)

                    logger.info(f"Subscription processed for payment {payment_id}")
                    logger.info(f"Payment {payment_id} captured successfully")

            except Exception as e:
                logger.error(f"Failed to capture payment {payment_id}: {str(e)}")
                raise

        elif payment_status == PaymentStatus.SUCCEEDED.value:
            logger.info(f"Payment {payment_id} already succeeded")

        elif payment_status == PaymentStatus.CANCELED.value:
            logger.warning(f"Payment {payment_id} was canceled")
            # Можно добавить логику для уведомления пользователя
            return

        elif payment_status == PaymentStatus.PENDING.value:
            # Если платёж всё ещё в ожидании, перезапускаем задачу
            pass

    except Exception as e:
        logger.error(f"Error processing payment {payment_id}: {str(e)}")
        raise
