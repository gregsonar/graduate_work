import os

RULE_TABLE = "rule"
TIME_TABLE = "timetable"


DSL = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("RULE_POSTGRES_USER"),
    "password": os.getenv("RULE_POSTGRES_PASSWORD"),
    "host": os.getenv("RULE_SQL_DB_HOST"),
    "port": os.getenv("RULE_SQL_PORT"),
}


AUTH_DSL = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("FLASK_DB_HOST_SLAVE"),
    "port": os.getenv("SQL_PORT"),
}


RABBIT_HOST = os.getenv("RABBITMQ_HOST")
RABBIT_USER = os.getenv("RABBITMQ_DEFAULT_USER")
RABBIT_PASS = os.getenv("RABBITMQ_DEFAULT_PASS")
RABBIT_RULE_MESSAGE_QUEUE = os.getenv("RABBIT_RULE_QUEUE")
