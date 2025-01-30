from notificator.email_processor import EmaiMessageProcessor
from notificator.notificator import Notificator
from psycopg2.extras import DictCursor

import config
from helpers import psycopg2_cursor_fetch_users
from logger import logger

PROCESS_USERS_BATCH_SIZE = 10_000

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
        subject='Theater'
    )

    @psycopg2_cursor_fetch_users
    def process_message(ch, method, properties, body, cursor: DictCursor) -> None:
        decoded_body = body.decode('utf-8')
        query = 'SELECT id, email, last_name, first_name FROM users'
        cursor.itersize = PROCESS_USERS_BATCH_SIZE
        cursor.execute(query)
        users = cursor.fetchall()
        for user in users:
            html = message_processor.render_template(
                'message.html',
                first_name=user['first_name'],
                last_name=user['last_name'],
                message=decoded_body,
            )
            sender = config.mailer_from_email
            subject = 'To out best viewer'
            message_processor.send_email(user['email'], sender, subject, html)
            message_processor.save_to_db(user_id=user['id'], message=decoded_body)

    notificator = Notificator(
        rabbit_host=config.rabbit_host,
        rabbit_user=config.rabbit_user,
        rabbit_pass=config.rabbit_pass,
        queue_name=config.rabbit_instant_message_to_all_queue,
        processor=process_message,
    )
    notificator.start_listening()
