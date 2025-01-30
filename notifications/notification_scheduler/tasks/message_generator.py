from typing import Generator
from dataclasses import dataclass

import psycopg2

from celery.utils.log import get_task_logger
from notification_scheduler.helpers.data_getter import TemplateDataGetter
from notification_scheduler.helpers.rabbit_mq import (
    send_message_to_queue,
    EmailMessage,
)
from notification_scheduler.settings.config import DSL, RULE_TABLE
from notification_scheduler.helpers.template_render import (
    render_template,
    UsersTemplateRender,
)


logger = get_task_logger(__name__)


def generate_messages(time_table_id):
    task_getter = TaskGetter(time_table_id)
    template_data_getter = TemplateDataGetter()
    for task in task_getter.get_task():
        render = UsersTemplateRender(
            task.template, template_data_getter, render_template
        )
        for text_message, user in render.gen_templates():
            send_message_to_queue(
                EmailMessage(
                    user=user, subject=task.subject, body=text_message
                )
            )


class TaskGetter:
    def __init__(self, time_table_id: str):
        self._time_table_id = time_table_id

    def get_task(self) -> Generator['Task', None, None]:
        with psycopg2.connect(**DSL) as conn, conn.cursor() as cursor:
            query = f'SELECT template, name, subject  FROM {RULE_TABLE} WHERE timetable_id = %s'
            cursor.execute(query, (self._time_table_id,))
            data = [el for el in cursor]
        for el in data:
            yield Task(template=el[0], name=el[1], subject=el[2])


@dataclass
class Task:
    template: str
    name: str
    subject: str
