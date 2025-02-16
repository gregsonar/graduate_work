from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Setting(BaseSettings):
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "billing_db"
    db_user: str = "admin"
    db_password: str = "123qwe"

    celery_broker_url: str = "redis://redis_billing:6380/0"

    yookassa_token: str = Field(default='1', env="YOOKASSA_TOKEN")
    yookassa_shopid: str = Field(default='1', env="YOOKASSA_SHOPID")

    check_delay_in_seconds: int = 5

    billing_username: str
    billing_password: str

    # Используем декоратор Field для явного указания, что это поле должно быть разрешено
    SUBSCRIPTIONS_URL: str = Field(default='http://auth_api:8000/api/v1/subscription')

    @property
    def dsn(self) -> str:
        return f'postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}'

    @property
    def dsn_sync(self) -> str:
        return f'postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}'

    class Config:
        env_prefix = "db_"
        env_file = ".env"
        extra = "allow"  # Это разрешит передачу любых дополнительных полей



# from pydantic_settings import BaseSettings, SettingsConfigDict
#
#
# class PostgresSettings(BaseSettings):
#     host: str = "postgres"
#     port: int = 5432
#     name: str = "billing_db"
#     user: str = "admin"
#     password: str = "123qwe"
#
#     model_config = SettingsConfigDict(env_prefix="db_", env_file=".env")
#
#
# class CelerySettings(BaseSettings):
#     broker_url: str
#
#     model_config = SettingsConfigDict(env_prefix="celery_", env_file=".env")
#
# class Setting(BaseSettings):
#     postgres: PostgresSettings = PostgresSettings()
#     celery: CelerySettings = CelerySettings()
#     dsn: str = f'postgresql+asyncpg://{postgres.user}:{postgres.password}@{postgres.host}:{postgres.port}/{postgres.name}'
#     dsn_sync: str = f'postgresql://{postgres.user}:{postgres.password}@{postgres.host}:{postgres.port}/{postgres.name}'
#     yookassa_token: str
#     yookassa_shopid: str
#
#     SUBSCRIPTIONS_URL: str = 'http://auth_api:8000/api/v1/subscription'
#
#     check_delay_in_seconds: int = 60
#
#
settings = Setting()
