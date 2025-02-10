from enum import Enum
from fastapi import HTTPException, status

class ErrorCode(str, Enum):
    SUBSCRIPTION_NOT_FOUND = "SUBSCRIPTION_NOT_FOUND"
    INVALID_STATUS_TRANSITION = "INVALID_STATUS_TRANSITION"
    SUBSCRIPTION_ALREADY_ACTIVE = "SUBSCRIPTION_ALREADY_ACTIVE"
    SUBSCRIPTION_ALREADY_SUSPENDED = "SUBSCRIPTION_ALREADY_SUSPENDED"
    SUBSCRIPTION_ALREADY_CANCELLED = "SUBSCRIPTION_ALREADY_CANCELLED"
    INVALID_DATES = "INVALID_DATES"
    USER_NOT_FOUND = "USER_NOT_FOUND"

class SubscriptionNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
            headers={"X-Error-Code": ErrorCode.SUBSCRIPTION_NOT_FOUND}
        )

class InvalidStatusTransitionException(HTTPException):
    def __init__(self, current_status: str, requested_status: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {current_status} to {requested_status}",
            headers={"X-Error-Code": ErrorCode.INVALID_STATUS_TRANSITION}
        )

class SubscriptionStateException(HTTPException):
    def __init__(self, message: str, error_code: ErrorCode):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
            headers={"X-Error-Code": error_code}
        )