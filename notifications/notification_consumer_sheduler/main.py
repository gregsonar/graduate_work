from notificator.email_processor import EmaiMessageProcessor
from notificator.notificator import Notificator

import config
from logger import logger

if __name__ == '__main__':
    message_processor = EmaiMessageProcessor(
        logger=logger,
        mailer_host=config.mailer_host,
        mailer_port=config.mailer_port,
        mailer_user=config.mailer_user,
        mailer_pass=config.mailer_password,
        sender_email=config.mailer_from_email,
        dsl=config.dsl_for_notifications,
        message_table_name=config.notifications_table_name,
        templates_dir='templates',
        template_name='message.html',
        subject='Welcome to out perfect theater'
    )

    notificator = Notificator(
        rabbit_host=config.rabbit_host,
        rabbit_user=config.rabbit_user,
        rabbit_pass=config.rabbit_pass,
        queue_name=config.rabbit_rule_queue,
        processor=message_processor.process_message,
    )
    notificator.start_listening()
