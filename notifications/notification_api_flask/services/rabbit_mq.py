import json

import pika

from settings.config import (
    RABBIT_HOST,
    RABBIT_USER,
    RABBIT_PASS,
    RABBIT_USER_CREATED_QUEUE,
    RABBIT_INSTANT_MESSAGE_TO_ALL_QUEUE,
    RABBIT_INSTANT_MESSAGE_EMAIL,
    RABBIT_INSTANT_MESSAGE_WEB_SOCKET,
)
from settings.extensions import logger
from services.serialization_schemas import Message, MessageType, MessageSchema


def send_to_queue(queue_name: str, message: bytes) -> None:
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST, credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=message,
        properties=pika.BasicProperties(delivery_mode=2),
    )
    connection.close()


def send_user_created_event(user_to_queue: dict) -> None:
    user_data = json.dumps(user_to_queue).encode('utf-8')
    send_to_queue(queue_name=RABBIT_USER_CREATED_QUEUE, message=user_data)
    logger.info(f'User created invitation sent. User: {user_to_queue}')


def send_instant_message_from_moderator(message: str) -> None:
    send_to_queue(
        queue_name=RABBIT_INSTANT_MESSAGE_TO_ALL_QUEUE,
        message=message.encode('utf-8'),
    )
    logger.info(f'Message to all users has been sent. Message {message}')


def send_instant_message(message: Message) -> None:
    queue = RABBIT_INSTANT_MESSAGE_EMAIL

    if message.message_type == MessageType.WEBSOCKET:
        queue = f'{RABBIT_INSTANT_MESSAGE_WEB_SOCKET}.{message.user_id}'
        body = message.body
    else:
        form_schema = MessageSchema()
        body = json.dumps(form_schema.dump(message)).encode('utf-8')

    send_to_queue(queue_name=queue, message=body)
    logger.info(
        f'Message to user {message.user_id} has been send. Message {message}'
    )
