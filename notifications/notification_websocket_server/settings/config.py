import os

RABBIT_HOST = os.getenv("RABBITMQ_HOST")
RABBIT_USER = os.getenv("RABBITMQ_DEFAULT_USER")
RABBIT_PASS = os.getenv("RABBITMQ_DEFAULT_PASS")
RABBIT_USER_INSTANT_MESSAGE_QUEUE = os.getenv("RABBIT_INSTANT_MESSAGE_WEB_SOCKET")

MESSAGES_DSL = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("NOTIFICATION_DB_HOST"),
    "port": os.getenv("SQL_PORT"),
}
