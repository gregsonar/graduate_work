from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from auth.models.user_account import SocialProvider
from auth.schemas.entity import BaseResponse

from .vk_oauth_schema import (
    SocialAccountBase,
    SocialAccountCreate,
    SocialAccountResponse
)


class AuthUrlResponse(BaseResponse):
    """
    Схема ответа с URL для авторизации через Yandex
    """

    auth_url: str = Field(..., description="URL для авторизации через Yandex")
    state: str = Field(
        ..., description="Случайная строка для защиты от CSRF атак", min_length=32
    )

    class Config:
        json_schema_extra = {
            "example": {
                "auth_url": "https://id.vk.com/authorize?client_id=12345&redirect_uri=https://example.com/callback&response_type=code&scope=email&v=5.131&state=abc123def456&code_challenge=xyz789&code_challenge_method=S256",
                "state": "abc123def456...",
            }
        }


class SocialAccountList(BaseModel):
    """
    Схема для списка социальных аккаунтов пользователя.
    """

    accounts: List[SocialAccountResponse] = Field(
        description="Список привязанных социальных аккаунтов",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "accounts": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "provider": "vk",
                        "social_id": "12345678",
                        "social_username": "john_doe",
                        "social_email": "john@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "avatar_url": "https://example.com/avatar.jpg",
                        "is_primary": True,
                        "created_at": "2024-01-01T12:00:00",
                        "updated_at": "2024-01-01T12:00:00",
                        "token_expires_at": "2024-12-31T23:59:59",
                    },
                    {
                        "id": "660e8400-e29b-41d4-a716-446655440000",
                        "provider": "google",
                        "social_id": "87654321",
                        "social_username": "john.doe",
                        "social_email": "john@gmail.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "avatar_url": "https://example.com/google_avatar.jpg",
                        "is_primary": False,
                        "created_at": "2024-01-02T12:00:00",
                        "updated_at": "2024-01-02T12:00:00",
                        "token_expires_at": "2024-12-31T23:59:59",
                    },
                ]
            }
        }


class YandexCallbackRequest(BaseResponse):
    """
    Схема для параметров callback запроса от Yandex
    """

    code: str = Field(..., description="Код авторизации от Yandex")
    state: str = Field(
        ..., description="Строка state, переданная при инициации авторизации"
    )
    error: Optional[str] = Field(
        None, description="Код ошибки, если авторизация не удалась"
    )
    error_description: Optional[str] = Field(None, description="Описание ошибки")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "def456...",
                "state": "abc123def456...",
                "error": "access_denied",
                "error_description": "User denied access",
            }
        }
