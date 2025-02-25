import os

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()

print(os.getenv("DB_PASSWORD"))


class Setting(BaseSettings):
    db_name: str = os.getenv("DB_NAME", "billing_db")
    db_user: str = os.getenv("DB_USER", "admin")
    db_password: str = os.getenv("DB_PASSWORD", "password")
    db_host: str = os.getenv("DB_HOST", "postgres")
    db_port: int = os.getenv("DB_PORT", 5432)

    celery_broker_url: str = os.getenv("DB_CELERY_BROKER_URL", "redis://redis_billing:6380/0")

    yookassa_shopid: str = Field(os.getenv("YOOKASSA_SHOP_ID"))
    yookassa_token: str = Field(
        os.getenv("YOOKASSA_API_KEY")
    )

    check_delay_in_seconds: int = 5

    # Используем декоратор Field для явного указания,
    # что это поле должно быть разрешено
    base_url: str = Field(
        os.getenv("DB_BASE_URL", "http://0.0.0.0/api/subscriptions/api/v1/subscription/")
    )
    auth_url: str = Field(
        os.getenv("DB_AUTH_URL", "http://auth_api:8000/api/v1/auth/me")
    )

    @property
    def dsn(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/"
            f"{self.db_name}"
        )

    @property
    def dsn_sync(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}"
            f":{self.db_port}/{self.db_name}"
        )

    class Config:
        env_prefix = "db_"
        env_file = ".env"
        extra = "allow"


settings = Setting()
