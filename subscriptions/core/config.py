# subscriptions/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Database
    POSTGRES_HOST: str = Field('localhost', alias='SUB_POSTGRES_HOST')
    POSTGRES_PORT: int = Field(5432, alias='SUB_POSTGRES_PORT')
    POSTGRES_DB: str = Field('subscription_db', alias='SUB_POSTGRES_DB')
    POSTGRES_USER: str = Field('app', alias='SUB_POSTGRES_USER')
    POSTGRES_PASSWORD: str = Field('123qwe', alias='SUB_POSTGRES_PASSWORD')

    @property
    def database_url(self) -> str:
        return f'postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'


settings = Settings()