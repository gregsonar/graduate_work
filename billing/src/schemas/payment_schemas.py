from uuid import UUID

from pydantic import BaseModel


class CreatePaymentSchema(BaseModel):
    tariff_id: UUID


class CreatedPaymentSchema(BaseModel):
    redirect_url: str
