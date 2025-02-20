from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TariffSchema(BaseModel):
    """Schema for tariff details"""
    id: UUID = Field(description="Unique identifier of the tariff")
    name: str = Field(description="Name of the tariff")
    description: str = Field(description="Description of the tariff")
    price: int = Field(description="Price of the tariff")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Standard",
                "description": "Basic tariff plan",
                "price": 99
            }
        }
    )


class PaymentSchema(BaseModel):
    """Schema for payment details"""
    id: UUID = Field(description="Unique identifier of the payment")
    user_id: UUID = Field(description="User ID associated with the payment")
    tariff_id: UUID = Field(description="Tariff ID associated with the payment")
    status: str = Field(
        description="Current status of the payment",
        examples=["pending", "succeeded", "canceled", "waiting_for_capture"],
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "tariff_id": "123e4567-e89b-12d3-a456-426614174002",
                "status": "paid"
            }
        }
    )
