from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreatePaymentSchema(BaseModel):
    tariff_id: UUID = Field(description="UUID to tariff")


class CreatedPaymentSchema(BaseModel):
    redirect_url: str = Field(description="URL to YooKasa payment")


# Responses for specific status codes
class DetailResponse(BaseModel):
    """Generic detail response"""
    detail: str = Field(description="Response message")
    code: str = Field(description="Operation code")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Operation completed successfully",
                "code": "SUCCESS"
            }
        }
    )


class SubscriptionCancel(BaseModel):
    """Schema for cancelling a subscription"""
    refund: bool = Field(
        default=False,
        description="Should I cancel with a refund or not"
    )
    reason: str = Field(
        description="Reason for cancellation",
        min_length=5,
        max_length=200,
        examples=["User requested cancellation", "Terms violation"]
    )
    immediate: bool = Field(
        default=False,
        description="Whether to cancel immediately or at period end"
    )
