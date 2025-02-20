import json
import pika
from dataclasses import dataclass
from typing import Dict
from uuid import UUID
import logging

from auth.core.config import RabbitMQSettings

logger = logging.getLogger(__name__)


@dataclass
class UserCreatedEvent:
    user_id: UUID
    email: str
    
    def to_json(self) -> str:
        return json.dumps({
            'user_id': str(self.user_id),
            'email': str(self.email)
        })


class UserEventProducer:
    def __init__(self, rabbit_config: RabbitMQSettings):  # Указываем тип
        self.rabbit_config = rabbit_config

    def _get_connection(self):
        credentials = pika.PlainCredentials(
            self.rabbit_config.user,  # Используем как атрибут
            self.rabbit_config.password  # Используем как атрибут
        )
        return pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.rabbit_config.host,  # Используем как атрибут
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
        )

    def publish_user_created(self, event: UserCreatedEvent):
        connection = None
        try:
            logger.info(f"Attempting to publish user created event for user {event.user_id}")
            connection = self._get_connection()
            channel = connection.channel()

            queue_name = self.rabbit_config.user_created_queue  # Используем как атрибут
            logger.info(f"Declaring queue {queue_name}")

            channel.queue_declare(
                queue=queue_name,
                durable=True
            )

            message = event.to_json()
            logger.info(f"Publishing message: {message}")

            channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            logger.info("Message published successfully")

        except Exception as e:
            logger.error(f"Failed to publish message: {str(e)}")
            raise
        finally:
            if connection and not connection.is_closed:
                connection.close()