from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    host: str = "postgres"
    port: int = 5432
    name: str = "billing_db"
    user: str = "admin"
    password: str = "123qwe"

    model_config = SettingsConfigDict(env_prefix="db_", env_file=".env")


class CelerySettings(BaseSettings):
    broker_url: str

    model_config = SettingsConfigDict(env_prefix="celery_", env_file=".env")

class Setting(BaseSettings):
    postgres: PostgresSettings = PostgresSettings()
    celery: CelerySettings = CelerySettings()
    dsn: str = f'postgresql+asyncpg://{postgres.user}:{postgres.password}@{postgres.host}:{postgres.port}/{postgres.name}'
    dsn_sync: str = f'postgresql://{postgres.user}:{postgres.password}@{postgres.host}:{postgres.port}/{postgres.name}'
    yookassa_token: str
    yookassa_shopid: str
    webhook_api_url: str
    payment_redirect_url: str

    AUTH_API_SUBSCRIBE_URL: str = ""
    AUTH_API_UNSUBSCRIBE_URL: str = ""
    #
    # header_key: str = "x-api-key"
    # header_value: str = "11111"
    #
    # auto_pay_delay: int = 60
    # check_delay_in_seconds: int = 60


settings = Setting()
