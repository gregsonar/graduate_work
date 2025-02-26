import json
from typing import Dict

import config
from logger import logger
from models import User
from notificator.email_processor import EmaiMessageProcessor
from notificator.notificator import Notificator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class UserConsumer:
    def __init__(self):
        self.engine = create_engine(config.dsl_for_notifications)
        self.Session = sessionmaker(bind=self.engine)

    def process_message(self, message: Dict):
        try:
            session = self.Session()

            # Создаем пользователя в БД уведомлений
            user = User(id=message["user_id"], email=message["email"])

            session.add(user)
            session.commit()

            logger.info(f"User {user.id} successfully saved to notifications DB")

            # После сохранения пользователя, отправляем приветственное письмо
            message_processor = EmaiMessageProcessor(
                logger=logger,
                mailer_host=config.mailer_host,
                mailer_port=config.mailer_port,
                mailer_user=config.mailer_user,
                mailer_pass=config.mailer_password,
                sender_email=config.mailer_from_email,
                dsl=config.dsl_for_notifications,
                message_table_name=config.notifications_table_name,
                templates_dir="templates",
                template_name="welcome.html",
                subject="Welcome to our perfect theater",
            )

            message_processor.process_message(message)

        except Exception as e:
            logger.error(f"Error processing user message: {e}")
            raise
        finally:
            session.close()


if __name__ == "__main__":
    consumer = UserConsumer()

    notificator = Notificator(
        rabbit_host=config.rabbit_host,
        rabbit_user=config.rabbit_user,
        rabbit_pass=config.rabbit_pass,
        queue_name=config.rabbit_user_created_queue_name,
        processor=consumer.process_message,
    )

    notificator.start_listening()
