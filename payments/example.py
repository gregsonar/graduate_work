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
        # Для успешных платежей используем тестовую карту 5555 5555 5555 4444 или кошелёк
        # Для отмены транзакции на стороне ЮКассы используем карту 4119 0988 7879 6485 (причина отмены: fraud_suspected)
        idempotence_key = uuid.uuid4()
        payment = provider.create_payment(
            amount=100.00,
            description="Успешный тестовый платеж",
            save_payment_method=True,
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
            elif current_status == 'pending':
                print("Платёж в обработке (pending).")
            elif current_status == 'canceled':
                print("Платёж отклонён (canceled)!")
                break
            else:
                raise PaymentCaptureError('Ошибка принятия платежа')

    except PaymentCreationError as e:
        print(f"Ошибка: {e}")

    except (MaxRetryError, TimeoutError) as network_error:
        print(f'Проблемы с сетью: {network_error}')


def demo_cancelled_by_shop_payment():
    print("\n=== ТЕСТ 2: ОТМЕНА ПЛАТЕЖА С НАШЕЙ СТОРОНЫ ===")

    current_status = None
    try:
        # Для успешных платежей используем тестовую карту 5555 5555 5555 4444 или кошелёк
        # Для отмены транзакции на стороне ЮКассы используем карту 4119 0988 7879 6485 (причина отмены: fraud_suspected)
        idempotence_key = uuid.uuid4()
        payment = provider.create_payment(
            amount=100.00,
            description="Успешный тестовый платеж",
            metadata={  # https://yookassa.ru/developers/api#create_payment_metadata
                "some_key": "some_value",
                "order_id": "123"
            },
            idempotence_key=idempotence_key
        )

        current_status = payment['status']
        if current_status == 'pending':
            print("Создан платеж:")
            pprint(payment)

        while True:
            input('Платёж произведён?')
            payment = provider.get_payment(payment['id'])
            current_status = payment['status']
            print(f"Статус платежа: {current_status}")
            if current_status == 'waiting_for_capture':
                print("\nПроизводим отмену платежа:")
                cancel = provider.cancel_payment(payment['id'])
                pprint(cancel)
                current_status = cancel['status']

            if current_status == 'canceled':
                print("Платёж отклонён (canceled)!")
                break

    except PaymentCreationError as e:
        print(f"Ошибка: {e}")

    except (MaxRetryError, TimeoutError) as network_error:
        print(f'Проблемы с сетью: {network_error}')


def demo_idempotency():
    print("\n=== ТЕСТ 3: ПРОВЕРКА ИДЕМПОТЕНТНОСТИ ===")

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


def demo_recurrent_payments():
    print("=== ТЕСТ 4: СОХРАНЕНИЕ ДАННЫХ И АВТОПЛАТЕЖ ===")
    current_status = None
    try:
        # Для успешных платежей используем тестовую карту 5555 5555 5555 4444 или кошелёк
        # Для отмены транзакции на стороне ЮКассы используем карту 4119 0988 7879 6485 (причина отмены: fraud_suspected)
        idempotence_key = uuid.uuid4()
        payment = provider.create_payment(
            amount=10.00,
            description="Оплата подписки",
            save_payment_method=True,
            metadata={  # https://yookassa.ru/developers/api#create_payment_metadata
                "some_key": "some_value",
                "order_id": "123"
            },
            idempotence_key=idempotence_key
        )
    except PaymentCreationError as e:
        print(f"Ошибка: {e}")

    current_status = payment['status']
    if current_status == 'pending':
        print("Создан платеж:")
        pprint(payment)

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
        elif current_status == 'pending':
            print("Платёж в обработке (pending).")
        elif current_status == 'canceled':
            print("Платёж отклонён (canceled)!")
            break
        else:
            raise PaymentCaptureError('Ошибка принятия платежа')

    while True:  # 2f3ef10f-000f-5000-8000-1289b76990f7
        print(f'Сохранённые данные платежа: {capture.payment_methods.id}')
        input('Повторить платёж?')
        recurrent_payment = provider.capture_payment(payment['id'])


if __name__ == "__main__":
    # demo_successful_payment()
    # print_separator()
    # demo_cancelled_by_shop_payment()
    # print_separator()
    # demo_idempotency()
    demo_recurrent_payments()
