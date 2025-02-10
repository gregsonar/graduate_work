import json
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from yookassa.domain.notification import WebhookNotification
from yookassa.domain.exceptions import ApiError
from providers.yookassa_provider import YooKassaProvider
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

provider = YooKassaProvider(
    account_id=os.getenv("YOOKASSA_SHOP_ID", "1234567"),
    secret_key=os.getenv("YOOKASSA_API_KEY", "test_apikey123")
)

@app.post("/webhook/yookassa")
async def yookassa_webhook(request: Request):
    try:
        event_json = await request.json()
        notification = WebhookNotification(event_json)
        payment = notification.object
        event_type = notification.event

        print(f"Получен вебхук: {event_type}")
        print(json.dumps(event_json, indent=4, ensure_ascii=False))

        if event_type == "payment.succeeded":
            print(f"Платеж {payment.id} успешно проведен.")
        elif event_type == "payment.waiting_for_capture":
            print(f"Платеж {payment.id} требует подтверждения. Подтверждаем...")
            provider.capture_payment(payment.id)
        elif event_type == "payment.canceled":
            print(f"Платеж {payment.id} отменен.")

        return {"status": "ok"}
    except ApiError as e:
        raise HTTPException(status_code=400, detail=f"Ошибка API: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка обработки вебхука: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8433)
