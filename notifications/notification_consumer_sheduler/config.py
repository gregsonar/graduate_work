import os

notifications_table_name = "notification_messages"

dsl_for_notifications = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("NOTIFICATION_DB_HOST"),
    "port": os.getenv("SQL_PORT"),
}

mailer_host = os.getenv("MAILER_HOST")
mailer_port = os.getenv("MAILER_PORT")
mailer_user = os.getenv("MAILER_USER")
mailer_password = os.getenv("MAILER_PASSWORD")
mailer_enc = os.getenv("MAILER_ENCRYPTION")
mailer_from_email = os.getenv("MAILER_FROM_EMAIL")

rabbit_host = os.getenv("RABBITMQ_HOST")
rabbit_user = os.getenv("RABBITMQ_DEFAULT_USER")
rabbit_pass = os.getenv("RABBITMQ_DEFAULT_PASS")
rabbit_rule_queue = os.getenv("RABBIT_RULE_QUEUE")
