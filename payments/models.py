# Pydantic-модели
from pydantic import BaseModel


class YooKassaPaymentRequest(BaseModel):
    amount: float
    currency: str = "RUB"
    description: str = ""
    metadata: dict = {}
    capture: bool = True


class YooKassaWebhook(BaseModel):
    event: str
    object: dict
