import os
from logging import config as logging_config
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .logger import LOGGING

load_dotenv()

# logging_config.dictConfig(LOGGING)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class RabbitMQSettings(BaseSettings):
    host: str = Field(default="localhost", alias="RABBITMQ_HOST")
    user: str = Field(..., alias="RABBITMQ_USER")
    password: str = Field(..., alias="RABBITMQ_PASS")
    user_created_queue: str = Field(..., alias="RABBIT_USER_CREATED_QUEUE")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


rabbit_config = RabbitMQSettings()


class OAuthProviderSettings(BaseModel):
    """Base settings for OAuth providers"""

    client_id: str
    client_secret: str
    redirect_url: str

    # Optional common settings
    api_version: Optional[str] = None
    auth_url: str
    token_url: str
    user_info_url: str


class VKOAuthSettings(OAuthProviderSettings):
    """VK specific OAuth settings"""

    # client_id: str = Field(..., alias="VK_CLIENT_ID")
    # client_secret: str = Field(..., alias="VK_CLIENT_SECRET")
    # redirect_url: str = Field(..., alias="VK_REDIRECT_URL")
    api_version: str = "5.131"
    auth_url: str = "https://id.vk.com/authorize"
    token_url: str = "https://id.vk.com/oauth2/auth"
    user_info_url: str = "https://id.vk.com/oauth2/user_info"


class YandexOAuthSettings(OAuthProviderSettings):
    """Yandex specific OAuth settings"""

    # client_id: str = Field(..., alias="YANDEX_CLIENT_ID")
    # client_secret: str = Field(..., alias="YANDEX_CLIENT_SECRET")
    # redirect_url: str = Field(..., alias="YANDEX_REDIRECT_URL")
    auth_url: str = "https://oauth.yandex.ru/authorize"
    token_url: str = "https://oauth.yandex.ru/token"
    user_info_url: str = "https://login.yandex.ru/info"


class OAuthConfig(BaseSettings):
    """OAuth configuration container"""

    vk: VKOAuthSettings
    yandex: YandexOAuthSettings

    @classmethod
    def from_general_config(cls, config: "Config") -> "OAuthConfig":
        """Creates OAuth config from general config"""
        return cls(
            vk=VKOAuthSettings(
                client_id=config.vk_client_id,
                client_secret=config.vk_client_secret,
                redirect_url=config.vk_redirect_url,
            ),
            yandex=YandexOAuthSettings(
                client_id=config.yandex_client_id,
                client_secret=config.yandex_client_secret,
                redirect_url=config.yandex_redirect_url,
            ),
        )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class TokenConfig(BaseSettings):
    """Configuration for token generation and validation"""

    secret_key: str = Field(..., alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class RedisSettings(BaseSettings):
    """Модель валидирующая конфиги Redis из .env файла."""

    host: str = Field(default="localhost", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="REDIS_PORT")
    db: int = Field(default=0, alias="REDIS_DATABASES")

    model_config = SettingsConfigDict(
        extra="ignore", env_file_encoding="utf-8", populate_by_name=True
    )


class Config(BaseSettings):
    """Модель валидирующая конфиги из .env файла."""

    db_host: str = Field("localhost", alias="POSTGRES_HOST")
    db_port: int = Field(..., alias="POSTGRES_PORT")
    db_user: str = Field(..., alias="POSTGRES_USER")
    db_password: str = Field(..., alias="POSTGRES_PASSWORD")
    db_name: str = Field(..., alias="POSTGRES_DB")

    jaeger_collector_endpoint: str = Field(..., alias="COLLECTOR_ENDPOINT")
    jaeger_collector_port: int = Field(..., alias="COLLECTOR_PORT")

    project_name: str = Field(..., alias="PROJECT_NAME")

    vk_client_id: str = Field(..., alias="VK_CLIENT_ID")
    vk_client_secret: str = Field(..., alias="VK_CLIENT_SECRET")
    vk_redirect_url: str = Field(..., alias="VK_REDIRECT_URL")

    yandex_client_id: str = Field(..., alias="YANDEX_CLIENT_ID")
    yandex_client_secret: str = Field(..., alias="YANDEX_CLIENT_SECRET")
    yandex_redirect_url: str = Field(..., alias="YANDEX_REDIRECT_URL")

    @property
    def db_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def oauth_config(self) -> OAuthConfig:
        return OAuthConfig.from_general_config(self)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


config = Config()
oauth_config = config.oauth_config
