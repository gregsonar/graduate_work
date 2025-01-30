from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from auth.models.user_account import SocialProvider
from auth.schemas.entity import BaseResponse


class SocialAccountBase(BaseModel):
    """
    Базовая схема для социального аккаунта.
    """
    provider: SocialProvider = Field(
        description="Провайдер социальной сети (vk, google, github, telegram)"
    )
    social_id: str = Field(
        description="Уникальный идентификатор пользователя в социальной сети"
    )
    social_username: Optional[str] = Field(
        None,
        description="Имя пользователя в социальной сети"
    )
    social_email: Optional[str] = Field(
        None,
        description="Email пользователя из социальной сети"
    )
    first_name: Optional[str] = Field(
        None,
        description="Имя пользователя"
    )
    last_name: Optional[str] = Field(
        None,
        description="Фамилия пользователя"
    )
    avatar_url: Optional[str] = Field(
        None,
        description="URL аватара пользователя"
    )
    is_primary: bool = Field(
        False,
        description="Является ли этот аккаунт основным способом входа",
    )

class SocialAccountCreate(SocialAccountBase):
    """
    Схема для создания нового социального аккаунта.
    Включает чувствительные данные, такие как токены.
    """
    access_token: str = Field(
        description="Токен доступа к API социальной сети"
    )
    refresh_token: Optional[str] = Field(
        None,
        description="Токен для обновления access token"
    )
    token_expires_at: Optional[datetime] = Field(
        None,
        description="Дата и время истечения срока действия токена"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Дополнительные метаданные от социальной сети"
    )

class SocialAccountResponse(SocialAccountBase):
    """
    Схема для ответа с данными социального аккаунта.
    Не включает чувствительные данные.
    """
    id: str = Field(
        description="Уникальный идентификатор записи в нашей системе",
    )
    created_at: datetime = Field(
        description="Дата и время создания записи"
    )
    updated_at: datetime = Field(
        description="Дата и время последнего обновления записи"
    )
    token_expires_at: Optional[datetime] = Field(
        None,
        description="Дата и время истечения срока действия токена",
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "provider": "vk",
                "social_id": "12345678",
                "social_username": "john_doe",
                "social_email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "avatar_url": "https://example.com/avatar.jpg",
                "is_primary": False,
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00",
                "token_expires_at": "2024-12-31T23:59:59"
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
                        "token_expires_at": "2024-12-31T23:59:59"
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
                        "token_expires_at": "2024-12-31T23:59:59"
                    }
                ]
            }
        }


class AuthUrlResponse(BaseResponse):
    """
    Схема ответа с URL для авторизации через Yandex
    """
    auth_url: str = Field(
        ...,
        description="URL для авторизации через Yandex"
    )
    state: str = Field(
        ...,
        description="Случайная строка для защиты от CSRF атак",
        min_length=32
    )

    class Config:
        json_schema_extra = {
            "example": {
                "auth_url": "https://id.example.com",
                "state": "abc123def456..."
            }
        }
