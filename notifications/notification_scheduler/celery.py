from celery import Celery
from notification_scheduler.tasks.message_generator import generate_messages
from notification_scheduler.tasks.tasks_generator import add_all_tasks

app = Celery(
    "notification_scheduler",
    broker="amqp://rabbit:rabbit@notification-rabbitmq//",
    include=[
        "notification_scheduler.tasks.tasks_generator",
        "notification_scheduler.tasks.message_generator",
    ],
)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    add_all_tasks(sender, send_message)


@app.task(bind=True)
def send_message(_, timetable_id: str):
    generate_messages(timetable_id)


if __name__ == "__main__":
    app.start()
