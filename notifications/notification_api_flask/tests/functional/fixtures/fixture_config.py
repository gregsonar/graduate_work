from pytest import fixture
from dataclasses import dataclass
from os import getenv


@dataclass
class ConfigDB:
    postgres_host: str
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_port: str

    def get_dns(self) -> dict:
        return {
            "dbname": self.postgres_db,
            "user": self.postgres_user,
            "password": self.postgres_password,
            "host": self.postgres_host,
            "port": self.postgres_port,
        }


@dataclass
class Config:
    db_config: ConfigDB
    auth_db_config: ConfigDB
    api_url: str


@fixture
def config() -> Config:
    return Config(
        db_config=ConfigDB(
            postgres_host=getenv("RULE_SQL_DB_HOST", "168.30.0.4"),
            postgres_db=getenv("RULE_POSTGRES_DB", "theater"),
            postgres_user=getenv("RULE_POSTGRES_USER", "postgres"),
            postgres_password=getenv("RULE_POSTGRES_PASSWORD", "secret"),
            postgres_port=getenv(
                "RULE_SQL_PORT",
            ),
        ),
        auth_db_config=ConfigDB(
            postgres_host=getenv("FLASK_DB_HOST_SLAVE", "168.30.0.4"),
            postgres_db=getenv("POSTGRES_DB", "theater"),
            postgres_user=getenv("POSTGRES_USER", "postgres"),
            postgres_password=getenv("POSTGRES_PASSWORD", "secret"),
            postgres_port=getenv(
                "SQL_PORT",
            ),
        ),
        api_url=getenv("NOTIFICATION_API_URL", "http://192.168.144.7:4000"),
    )
