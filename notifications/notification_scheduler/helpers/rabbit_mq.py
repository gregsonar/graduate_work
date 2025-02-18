import json
from dataclasses import dataclass

import pika
from pika import BlockingConnection
from pika.adapters.blocking_connection import BlockingChannel
from notification_scheduler.helpers.data_getter import User

from notification_scheduler.settings.config import (
    RABBIT_HOST,
    RABBIT_USER,
    RABBIT_PASS,
    RABBIT_RULE_MESSAGE_QUEUE,
)


def prep_conn(queue_name: str) -> (BlockingConnection, BlockingChannel):
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST, credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    return connection, channel


def send_message_to_queue(message: "EmailMessage") -> None:
    connection, channel = prep_conn(queue_name=RABBIT_RULE_MESSAGE_QUEUE)
    channel.basic_publish(
        exchange="",
        routing_key=RABBIT_RULE_MESSAGE_QUEUE,
        body=message.serialize("utf-8"),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    connection.close()


@dataclass
class EmailMessage:
    user: "User"
    subject: str
    body: str

    def serialize(self, encoding: str = "utf-8") -> bytes:
        return json.dumps(
            {
                "user": self.user.to_dict(),
                "subject": self.subject,
                "body": self.body,
            }
        ).encode(encoding)
