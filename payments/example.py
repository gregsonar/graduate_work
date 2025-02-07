import uuid
from pprint import pprint
from providers.yookassa_provider import YooKassaProvider
from exceptions import PaymentCreationError, PaymentCaptureError
from urllib3.exceptions import MaxRetryError, TimeoutError
from dotenv import load_dotenv
import os

load_dotenv()

# Инициализация провайдера с тестовыми данными
provider = YooKassaProvider(
    account_id=os.getenv("YOOKASSA_SHOP_ID", "1234567"),
    secret_key=os.getenv("YOOKASSA_API_KEY", "test_apikey123")
)


def print_separator():
    print("\n" + "=" * 80 + "\n")


def simulate_webhook(payment_id: str, event: str):
    """Имитация получения вебхука от ЮKassa"""
    print(f"\nИмитируем вебхук: {event}")
    webhook_data = {
        "event": event,
        "object": {
            "id": payment_id,
            "status": event.split('.')[-1],
            "amount": {"value": "100.00", "currency": "RUB"},
            "metadata": {"order_id": "123"},
            "confirmation": {"confirmation_url": "https://example.com"}
        }
    }
    provider.handle_webhook(webhook_data['event'], webhook_data['object'])


def demo_successful_payment():
    print("=== ТЕСТ 1: УСПЕШНЫЙ ПЛАТЕЖ ===")
    current_status = None
    try:
        # Создаем платеж с тестовой картой 5555 5555 5555 4444
        idempotence_key = uuid.uuid4()
        payment = provider.create_payment(
            amount=100.00,
            description="Успешный тестовый платеж",
            metadata={ # https://yookassa.ru/developers/api#create_payment_metadata
                "some_key": "some_value",
                "order_id": "123"
            },
            idempotence_key=idempotence_key
        )

        current_status = payment['status']
        if current_status == 'pending':
            print("Создан платеж:")
            pprint(payment)

        # Имитируем успешный вебхук
        # simulate_webhook(payment['id'], "payment.succeeded")

        # # Проверяем статус
        # print("\nПроверяем статус платежа:")
        # payment = provider.get_payment(payment['id'])
        # current_status = payment['status']

        while True:
            input('Платёж произведён?')
            payment = provider.get_payment(payment['id'])
            current_status = payment['status']
            print(f"Статус платежа: {current_status}")
            if current_status == 'waiting_for_capture':
                print("\nПроизводим принятие платежа:")
                capture = provider.capture_payment(payment['id'])
                pprint(capture)
                current_status = capture['status']
                if current_status == 'succeeded':
                    print("Платёж успешно проведён")
                    break
                else:
                    raise PaymentCaptureError('Ошибка принятия платежа')

    except PaymentCreationError as e:
        print(f"Ошибка: {e}")

    except (MaxRetryError, TimeoutError) as network_error:
        print(f'Проблемы с сетью: {network_error}')


def demo_pending_capture():
    print("\n=== ТЕСТ 2: ПЛАТЕЖ ТРЕБУЕТ ПОДТВЕРЖДЕНИЯ ===")

    try:
        # Создаем платеж с тестовой картой 2200 0000 0000 0004
        payment = provider.create_payment(
            amount=200.00,
            description="Платеж требует подтверждения",
            metadata={
                "card": "2200000000000004",
                "order_id": "456"
            },
            capture=True,  # Не подтверждаем автоматически https://yookassa.ru/developers/api#create_payment_capture
            idempotence_key=uuid.uuid4()
        )

        print("Создан платеж:")
        pprint(payment)

        # Имитируем вебхук ожидания подтверждения
        # simulate_webhook(payment['id'], "payment.waiting_for_capture")

        # Подтверждаем платеж вручную
        print("\nПодтверждаем платеж:")
        captured_payment = provider.capture_payment(payment['id'])
        pprint(captured_payment)

    except PaymentCaptureError as e:
        print(f"Ошибка подтверждения: {e}")


def demo_failed_payment():
    print("\n=== ТЕСТ 3: ОШИБКА ПЛАТЕЖА ===")

    try:
        # Пытаемся создать платеж с невалидными данными
        payment = provider.create_payment(
            amount=300.00,
            description="Неудачный платеж",
            metadata={
                "card": "2200000000000005",  # Карта для отклоненных платежей
                "order_id": "789"
            },
            idempotence_key=uuid.uuid4()
        )

    except PaymentCreationError as e:
        print(f"Поймана ожидаемая ошибка: {e}")

        # Имитируем вебхук отмены
        simulate_webhook("dummy_id", "payment.canceled")


def demo_idempotency():
    print("\n=== ТЕСТ 4: ПРОВЕРКА ИДЕМПОТЕНТНОСТИ ===")

    key = uuid.uuid4()

    try:
        # Первый запрос
        payment1 = provider.create_payment(
            amount=100.00,
            description="Тест идемпотентности",
            idempotence_key=key
        )

        # Повторный запрос с тем же ключом
        payment2 = provider.create_payment(
            amount=100.00,
            description="Тест идемпотентности",
            idempotence_key=key
        )

        print("Результаты должны быть идентичны:")
        print(f"Payment 1 ID: {payment1['id']}")
        print(f"Payment 2 ID: {payment2['id']}")

    except PaymentCreationError as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    demo_successful_payment()
    # print_separator()

    # demo_pending_capture()
    # print_separator()

    # demo_failed_payment()
    # print_separator()

    # demo_idempotency()