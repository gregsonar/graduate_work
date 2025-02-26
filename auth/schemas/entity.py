from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """User registration request schema"""

    username: str = Field(
        ..., min_length=3, max_length=50, description="Desired username for new account"
    )
    password: str = Field(..., description="Password for new account")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    is_superuser: Optional[bool] = Field(
        False, description="Flag indicating whether user is a superuser"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "secure_password123",
                "email": "john@example.com",
                "is_superuser": False,
            }
        }


class UserInDB(BaseModel):
    id: UUID
    first_name: str
    last_name: str

    class Config:
        from_attributes = True
