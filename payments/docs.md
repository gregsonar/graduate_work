# Процесс платежа:
0) Подключить платёжного провайдера
1) Создать платёж
2) Перенаправить пользователя на страницу оплаты
3) Проверить статус платежа:  # https://yookassa.ru/developers/payment-acceptance/getting-started/payment-process#lifecycle
   - 'pending' - ожидает оплаты
   - 'waiting_for_capture' - можно принимать на стороне магазина
   - 'succeeded' - успешно произведён и принят
   - 'canceled' - отменён магазином, истекло время на принятие платежа или платеж был отклонен ЮKassa или платежным провайдером
4) Принять платёж


## Подключение провайдера

```python
import os
from dotenv import load_dotenv
from providers.yookassa_provider import YooKassaProvider

load_dotenv()

provider = YooKassaProvider(
    account_id=os.getenv("YOOKASSA_SHOP_ID", "id магазина из лк ЮКассы"),
    secret_key=os.getenv("YOOKASSA_API_KEY", "test_apikey123")
)
```

## Создание платежа:
https://yookassa.ru/developers/api#create_payment
    
Минимальная версия:
```python
    provider.create_payment(100.53)
```

Расширенная версия:
```python 
    idempotence_key = uuid.uuid4()  # ключ для защиты от случайного повторения транзакций https://yookassa.ru/developers/using-api/interaction-format#idempotence
    payment = provider.create_payment(
        amount=100.00,
        description="Успешный тестовый платеж",
        metadata={  # Любые дополнгительные данные, которые можно пробросить в платёж https://yookassa.ru/developers/api#create_payment_metadata
            "order_id": "123"
        },
        idempotence_key=idempotence_key
    )
```
В ответ ЮКасса возвращает объект платежа:  # https://yookassa.ru/developers/api#payment_object
```json
    {
        "id": "2f384000-0000-0000-0000-1a1e89e00000",
        "status": "pending",
        "amount": {
            "value": "100.53",
            "currency": "RUB"
        },
        "recipient": {
            "account_id": "1023840",
            "gateway_id": "2395805"
        },
        "created_at": "2025-02-07T15:58:42.490Z",
        "confirmation": {
            "type": "redirect",
            "confirmation_url": "https://yoomoney.ru/checkout/payments/v2/contract?orderId=2f384000-0000-0000-0000-1a1e89e00000"
        },
        "test": true,
        "paid": false,
        "refundable": false,
        "metadata": {
            "cms_name": "yookassa_sdk_python"
        }
    }
```

## Редирект и статусы
В `confirmation_url` надо направить пользователя для оплаты (для тестов сходить самостоятельно, платёж проходит из тестового кошелька)

Статус платежа проверяется как `status = provider.get_payment(payment['id'])['status']`.

Возможные значения: `pending`, `waiting_for_capture`, `succeeded` и `canceled`. 
Если статус `waiting_for_capture`, значит ЮКасса получила деньги от пользователя (сделала холд, если точнее) и платёж можно принимать на нашей стороне:


## Приём платежа
`capture = provider.capture_payment(payment['id'])`

При успешном получении `capture['status']` должен быть `succeeded`

# _DEMO_
```python
payment = provider.create_payment(100.53)
status = provider.get_payment(payment['id'])['status']
# 'pending'

# Редиректим пользователя на адрес кассы:
payment['confirmation']['confirmation_url']
# https://yoomoney.ru/checkout/payments/v2/contract?orderId=2f38479d-...-17b8f48b1aee'

# После оплаты статус изменится:
provider.get_payment(payment['id'])['status']
# 'waiting_for_capture'

# Производим принятие платежа:
capture = provider.capture_payment(payment['id'])
current_status = capture['status']
# 'succeeded' - платёж успешно проведён!
```