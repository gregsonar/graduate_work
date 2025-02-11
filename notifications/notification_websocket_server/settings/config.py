import os


RABBIT_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBIT_USER = os.getenv('RABBITMQ_DEFAULT_USER', 'rabbit')
RABBIT_PASS = os.getenv('RABBITMQ_DEFAULT_PASS', 'rabbit')
RABBIT_USER_INSTANT_MESSAGE_QUEUE = os.getenv(
    'RABBIT_INSTANT_MESSAGE_WEB_SOCKET', '_websocket.plain_messages'
)

MESSAGES_DSL = {
    'database': os.getenv('POSTGRES_DB', 'postgres'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'secret'),
    'host': os.getenv('NOTIFICATION_DB_HOST', 'localhost'),
    'port': os.getenv('SQL_PORT', '5432'),
}
