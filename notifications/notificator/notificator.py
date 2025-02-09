import pika

from typing import Callable


class Notificator:
    def __init__(
        self,
        rabbit_host: str,
        rabbit_user: str,
        rabbit_pass: str,
        queue_name: str,
        processor: Callable,
    ) -> None:
        self.rabbit_user = rabbit_user
        self.rabbit_pass = rabbit_pass
        self.rabbit_host = rabbit_host
        self.queue_name = queue_name
        self.processor = processor

    def start_listening(self) -> None:
        credentials = pika.PlainCredentials(self.rabbit_user, self.rabbit_pass)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.rabbit_host, credentials=credentials
            )
        )
        channel = connection.channel()
        channel.queue_declare(queue=self.queue_name, durable=True)
        channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.processor,
            auto_ack=True,
        )
        channel.start_consuming()
