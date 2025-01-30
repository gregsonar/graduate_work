from pydantic import BaseModel, Field
from .entity import BaseResponse

class PasswordChangeRequest(BaseResponse):
    """Password change request schema"""
    current_password: str = Field(
        ...,
        # min_length=8,
        description="Current user password"
    )
    new_password: str = Field(
        ...,
        # min_length=8,
        description="New password"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "old_secure_password123",
                "new_password": "new_secure_password456"
            }
        }

class PasswordChangeResponse(BaseResponse):
    """Password change response schema"""
    detail: str = Field(
        ...,
        description="Password change operation result message"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Password successfully changed"
            }
        }