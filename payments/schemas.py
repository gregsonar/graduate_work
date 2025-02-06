from typing import Optional

from pydantic import BaseModel


class YooKassaPaymentSchema(BaseModel):
    id: str
    status: str
    amount: dict
    description: Optional[str]
    metadata: dict
    confirmation: dict


class YooKassaRefundSchema(BaseModel):
    id: str
    payment_id: str
    status: str
    amount: dict
