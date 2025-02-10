import uuid
import json
import smtplib

import psycopg2
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader


class EmaiMessageProcessor:
    def __init__(
        self,
        logger,
        templates_dir: str,
        mailer_host: str,
        mailer_port: str,
        mailer_user: str,
        mailer_pass: str,
        sender_email: str,
        dsl: dict,
        message_table_name: str,
        template_name: str,
        subject: str,
    ):
        self.logger = logger
        self.mailer_host = mailer_host
        self.mailer_port = mailer_port
        self.mailer_user = mailer_user
        self.mailer_pass = mailer_pass
        self.sender_email = sender_email
        self.dsl = dsl
        self.message_table_name = message_table_name
        self.templates_dir = templates_dir
        self.template_name = template_name
        self.subject = subject

    def render_template(self, template: str, **kwargs) -> str:
        template_env = Environment(loader=FileSystemLoader(self.templates_dir))
        templ = template_env.get_template(template)
        return templ.render(**kwargs)

    def send_email(
        self, to: str, sender: str, subject: str, body: str
    ) -> None:
        msg = MIMEMultipart('alternative')
        msg['From'] = sender
        msg['Subject'] = subject
        msg['To'] = to
        msg.attach(MIMEText(body, 'html'))
        server = smtplib.SMTP(self.mailer_host, self.mailer_port)
        server.login(self.mailer_user, self.mailer_pass)
        try:
            server.sendmail(sender, to, msg.as_string())
        except Exception as e:
            self.logger.error(e)
        finally:
            server.quit()

    def save_to_db(self, user_id: str, message: str) -> None:
        with psycopg2.connect(**self.dsl) as conn, conn.cursor() as cursor:
            query = (
                f'INSERT INTO {self.message_table_name} (id, user_id, message)'
                f' VALUES (%s, %s, %s)'
            )
            cursor.execute(query, (str(uuid.uuid4()), user_id, message))

    def process_message(self, ch, method, properties, body) -> None:
        user = json.loads(body)
        html = self.render_template(
            self.template_name,
            first_name=user.get('first_name') or '',
            last_name=user.get('last_name') or '',
        )
        sender = self.sender_email
        subject = self.subject
        email = user.get('email')
        if email:
            self.send_email(user['email'], sender, subject, html)
            self.save_to_db(user_id=user['id'], message=subject)
