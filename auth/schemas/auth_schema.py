from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from .entity import BaseResponse

class AuthRequest(BaseResponse):
    """Authentication request schema"""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username for authentication"
    )
    password: str = Field(
        ...,
        # min_length=8,
        description="User password"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "secure_password123"
            }
        }

class TokenResponse(BaseResponse):
    """Token response schema for authentication and refresh operations"""
    access_token: str = Field(
        ...,
        description="JWT access token for API authorization"
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token for obtaining new access tokens"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class CurrentUserResponse(BaseResponse):
    """Current user information response schema"""
    id: UUID = Field(
        ...,
        description="User's unique identifier"
    )
    username: str = Field(
        ...,
        description="User's username"
    )
    is_superuser: bool = Field(
        ...,
        description="Superuser status"
    )
    roles: List[str] = Field(
        ...,
        description="List of user's roles"
    )
    email: Optional[str] = Field(
        None,
        description="User's email address"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "john_doe",
                "is_superuser": False,
                "roles": ["user", "admin"],
                "email": "john@example.com",
                "created_at": "2024-01-01T00:00:00",
                "last_login": "2024-01-01T12:00:00"
            }
        }

class LogoutResponse(BaseResponse):
    """Logout response schema"""
    detail: str = Field(
        ...,
        description="Logout operation result message"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Successfully logged out"
            }
        }
