import os

RABBIT_HOST = os.getenv("RABBITMQ_HOST")
RABBIT_USER = os.getenv("RABBITMQ_DEFAULT_USER")
RABBIT_PASS = os.getenv("RABBITMQ_DEFAULT_PASS")
RABBIT_USER_CREATED_QUEUE = os.getenv("RABBIT_USER_CREATED_QUEUE")
RABBIT_INSTANT_MESSAGE_TO_ALL_QUEUE = os.getenv("RABBIT_INSTANT_MESSAGE_TO_ALL_QUEUE")
RABBIT_INSTANT_MESSAGE_EMAIL = os.getenv("RABBIT_INSTANT_MESSAGE_EMAIL")
RABBIT_INSTANT_MESSAGE_WEB_SOCKET = os.getenv("RABBIT_INSTANT_MESSAGE_WEB_SOCKET")


class BaseConfig:
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "secret01")
    SQLALCHEMY_DATABASE_URI = f'postgresql://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("FLASK_DB_HOST_SLAVE")}:{os.getenv("SQL_PORT")}/{os.getenv("POSTGRES_DB")}'
    SQLALCHEMY_BINDS = {
        "auth_sql": f'postgresql://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("FLASK_DB_HOST_SLAVE")}:{os.getenv("SQL_PORT")}/{os.getenv("POSTGRES_DB")}',
        "rule_sql": f'postgresql://{os.getenv("RULE_POSTGRES_USER")}:{os.getenv("RULE_POSTGRES_PASSWORD")}@{os.getenv("RULE_SQL_DB_HOST")}:{os.getenv("RULE_SQL_PORT")}/{os.getenv("POSTGRES_DB")}',
    }


class DevConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProdConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_ECHO = True


configurations = {"dev": DevConfig, "prod": ProdConfig}
