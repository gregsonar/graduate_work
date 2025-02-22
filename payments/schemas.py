from typing import Optional

from pydantic import BaseModel, Field


class AmountSchema(BaseModel):
    value: str
    currency: str


class YooKassaPaymentSchema(BaseModel, extra='allow'):
    id: str
    status: str
    amount: AmountSchema
    description: Optional[str] = Field(None, description="Описание платежа")
    metadata: dict
    confirmation: Optional[dict] = None


class YooKassaRefundSchema(BaseModel):
    id: str
    payment_id: str
    status: str
    amount: dict
