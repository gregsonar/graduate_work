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

    def get_db_connection(self):
        return psycopg2.connect(**self.dsl)

    def render_template(self, template: str, **kwargs) -> str:
        template_env = Environment(loader=FileSystemLoader(self.templates_dir))
        templ = template_env.get_template(template)
        return templ.render(**kwargs)

    def send_email(self, to: str, sender: str, subject: str, body: str) -> None:
        msg = MIMEMultipart("alternative")
        msg["From"] = sender
        msg["Subject"] = subject
        msg["To"] = to
        msg.attach(MIMEText(body, "html"))
        server = smtplib.SMTP(self.mailer_host, self.mailer_port)
        server.login(self.mailer_user, self.mailer_pass)
        try:
            server.sendmail(sender, to, msg.as_string())
            self.logger.info(f"Email sent successfully to {to}")
        except Exception as e:
            self.logger.error(f"Error sending email to {to}: {e}")
        finally:
            server.quit()

    def save_user(self, user_id: str, email: str) -> None:
        with self.get_db_connection() as conn, conn.cursor() as cursor:
            query = "INSERT INTO users (id, email) VALUES (%s, %s)"
            cursor.execute(query, (user_id, email))
            self.logger.info(f"User {user_id} saved to database")

    def save_to_db(self, user_id: str, message: str) -> None:
        with self.get_db_connection() as conn, conn.cursor() as cursor:
            query = (
                f"INSERT INTO {self.message_table_name} (id, user_id, message)"
                f" VALUES (%s, %s, %s)"
            )
            cursor.execute(query, (str(uuid.uuid4()), user_id, message))
            self.logger.info(f"Message saved to database for user {user_id}")

    def process_message(self, ch, method, properties, body) -> None:
        user = json.loads(body)
        email = user.get("email")
        user_id = user.get("user_id")

        if not email or not user_id:
            self.logger.error(f"Missing required fields: {body}")
            return

        # Сначала создаем пользователя
        try:
            self.save_user(user_id, email)
        except psycopg2.IntegrityError as e:
            if "duplicate key value violates unique constraint" in str(e):
                self.logger.info(f"User {user_id} already exists")
            else:
                self.logger.error(f"Error saving user: {e}")
                return
        except Exception as e:
            self.logger.error(f"Error saving user: {e}")
            return

        # Затем отправляем письмо и сохраняем уведомление
        html = self.render_template(
            self.template_name,
            first_name=user.get("first_name") or "",
            last_name=user.get("last_name") or "",
        )

        self.send_email(email, self.sender_email, self.subject, html)
        self.save_to_db(user_id=user_id, message=self.subject)
