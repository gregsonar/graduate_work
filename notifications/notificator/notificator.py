import logging
import pika
from typing import Callable
from pika.exceptions import AMQPConnectionError, AMQPChannelError


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
        try:
            logger.info(f"Подключение к RabbitMQ на {self.rabbit_host}")
            credentials = pika.PlainCredentials(self.rabbit_user, self.rabbit_pass)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.rabbit_host, credentials=credentials
                )
            )
            channel = connection.channel()

            logger.info(f"Объявление очереди {self.queue_name}")
            channel.queue_declare(queue=self.queue_name, durable=True)

            logger.info("Начало прослушивания сообщений")
            channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.processor,
                auto_ack=True,
            )
            channel.start_consuming()

        except AMQPConnectionError as e:
            logger.error(f"Ошибка подключения к RabbitMQ: {str(e)}")
            raise
        except AMQPChannelError as e:
            logger.error(f"Ошибка канала RabbitMQ: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {str(e)}")
            raise