from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "Subscription Service"

    # Database
    POSTGRES_HOST: str = Field("localhost", alias="SUB_POSTGRES_HOST")
    POSTGRES_PORT: int = Field(5432, alias="SUB_POSTGRES_PORT")
    POSTGRES_DB: str = Field("subscriptions_db", alias="SUB_POSTGRES_DB")
    POSTGRES_USER: str = Field("postgres", alias="SUB_POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field("secret", alias="SUB_POSTGRES_PASSWORD")

    ALLOWED_HOSTS: list = ["*"]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
