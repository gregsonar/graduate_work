from enum import Enum
from uuid import UUID
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict, model_validator, AwareDatetime

from subscriptions.models.subscription import SubscriptionPlanType, SubscriptionStatus


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    CANCELED = "canceled"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class SubscriptionBase(BaseModel):
    """Base subscription attributes"""

    plan_type: SubscriptionPlanType = Field(
        description="Type of subscription plan",
        examples=["basic", "standard", "premium"],
    )
    start_date: AwareDatetime = Field(
        description="Start date of subscription",
        examples=["2025-02-04 19:46:17.266259+00:00"],
    )
    end_date: AwareDatetime = Field(
        description="End date of subscription",
        examples=["2025-02-05 19:46:17.266259+00:00"],
    )
    price: Decimal = Field(
        description="Subscription price",
        max_digits=10,
        decimal_places=2,
        examples=[9.99, 19.99, 29.99],
    )
    is_auto_renewable: bool = Field(
        default=False, description="Whether subscription auto-renews"
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "SubscriptionBase":
        if self.start_date >= self.end_date:
            raise ValueError("end_date must be after start_date")
        return self


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating a new subscription"""

    user_id: UUID = Field(
        description="ID of the user owning the subscription",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )


class SubscriptionUpdate(BaseModel):
    """Schema for updating subscription details"""

    end_date: AwareDatetime | None = Field(
        default=None,
        description="New end date for subscription",
        examples=["2025-02-04 19:46:17.266259+00:00"],
    )
    is_auto_renewable: bool | None = Field(
        default=None, description="Update auto-renewal setting"
    )

    status: SubscriptionStatus | None = Field(
        default=SubscriptionStatus.ACTIVE,
        description="Subscription Status",
        examples=[SubscriptionStatus.ACTIVE, SubscriptionStatus.SUSPENDED],
    )


class SubscriptionSuspend(BaseModel):
    """Schema for suspending a subscription"""

    reason: str = Field(
        description="Reason for suspension",
        min_length=5,
        max_length=200,
        examples=["Payment failure", "User requested suspension"],
    )


class SubscriptionResume(BaseModel):
    """Schema for resuming a suspended subscription"""

    comment: str | None = Field(
        default=None,
        description="Optional comment for resumption",
        max_length=200,
        examples=["Payment issue resolved"],
    )


class SubscriptionCancel(BaseModel):
    """Schema for cancelling a subscription"""

    reason: str = Field(
        description="Reason for cancellation",
        min_length=5,
        max_length=200,
        examples=["User requested cancellation", "Terms violation"],
    )
    immediate: bool = Field(
        default=False, description="Whether to cancel immediately or at period end"
    )


class SubscriptionResponse(SubscriptionBase):
    """Schema for subscription response"""

    id: UUID = Field(description="Subscription unique identifier")
    user_id: UUID = Field(description="User ID associated with subscription")
    status: SubscriptionStatus = Field(
        description="Current status of subscription",
        examples=["active", "suspended", "cancelled"],
    )
    created_at: AwareDatetime = Field(description="Subscription creation timestamp")
    updated_at: AwareDatetime = Field(description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "plan_type": "premium",
                "status": "active",
                "start_date": "2025-02-04 19:46:17.266259+00:00",
                "end_date": "2024-03-04T00:00:00Z",
                "price": "29.99",
                "is_auto_renewable": True,
                "created_at": "2025-02-04 19:46:17.266259+00:00",
                "updated_at": "2025-02-04 19:46:17.266259+00:00",
            }
        },
    )


class SubscriptionHistoryResponse(BaseModel):
    """Schema for subscription history entries"""

    id: UUID = Field(description="History entry unique identifier")
    subscription_id: UUID = Field(description="Associated subscription ID")
    action: str = Field(
        description="Action performed on subscription",
        examples=["created", "suspended", "resumed", "cancelled"],
    )
    details: dict | None = Field(
        default=None, description="Additional details about the action"
    )
    created_at: AwareDatetime = Field(description="When this action occurred")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "subscription_id": "123e4567-e89b-12d3-a456-426614174000",
                "action": "suspended",
                "details": {"reason": "Payment failure"},
                "created_at": "2025-02-04 19:46:17.266259+00:00",
            }
        },
    )


# Responses for specific status codes
class DetailResponse(BaseModel):
    """Generic detail response"""

    detail: str = Field(description="Response message")
    code: str = Field(description="Operation code")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"detail": "Operation completed successfully", "code": "SUCCESS"}
        }
    )


class ErrorResponse(BaseModel):
    """Error response schema"""

    detail: str = Field(description="Error description")
    error_code: str = Field(description="Error code for client handling")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Subscription not found",
                "error_code": "SUBSCRIPTION_NOT_FOUND",
            }
        }
    )
