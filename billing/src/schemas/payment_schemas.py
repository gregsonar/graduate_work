from pydantic import BaseModel


class CreatedPaymentSchema(BaseModel):
    redirect_url: str