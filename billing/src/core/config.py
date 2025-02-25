from pydantic import Field
from pydantic_settings import BaseSettings


class Setting(BaseSettings):
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "billing_db"
    db_user: str = "admin"
    db_password: str = "123qwe"

    celery_broker_url: str = "redis://redis_billing:6380/0"

    yookassa_token: str = Field(
        default="test_xB8klULgAEuzogIqiJmKvdKLI5-9SOOTBxFYI6zOjZM"
    )
    yookassa_shopid: str = Field(default="1023840")

    check_delay_in_seconds: int = 5

    # Используем декоратор Field для явного указания,
    # что это поле должно быть разрешено
    base_url: str = Field(
        default="http://0.0.0.0/api/subscriptions/api/v1/subscription/"
    )
    auth_url: str = Field(default="http://auth_api:8000/api/v1/auth/me")

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
