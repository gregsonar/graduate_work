import datetime
from uuid import UUID

from pydantic import BaseModel


class TariffSchema(BaseModel):
    id: UUID
    name: str
    description: str
    price: int


class PaymentSchema(BaseModel):
    id: UUID
    user_id: UUID
    tariff_id: UUID
    status: str
