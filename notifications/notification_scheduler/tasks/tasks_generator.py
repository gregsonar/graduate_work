import psycopg2
from celery import Celery, Task
from celery.schedules import crontab
from psycopg2.extras import RealDictCursor

from notification_scheduler.helpers.data_getter import TimeTable
from notification_scheduler.settings.config import DSL, TIME_TABLE
from notification_scheduler.settings.extensions import logger


TIME_TABLE_IDS = {}


def add_all_tasks(app: Celery, task):
    all_timetable = get_all_timetable()
    for timetable_id, timetable in all_timetable.items():
        add_periodic_task(app, task, timetable)


def get_all_timetable() -> dict:
    with psycopg2.connect(
        **DSL, cursor_factory=RealDictCursor
    ) as conn, conn.cursor() as cursor:
        query = f'SELECT id, min, h, day, month, week_day  FROM {TIME_TABLE}'
        cursor.execute(query)
        all_tasks = [TimeTable(**record) for record in cursor]
        logger.info(f'get data: %s', len(all_tasks))
    if not all_tasks:
        return {}

    return {task.id: task for task in all_tasks}


def add_periodic_task(app: Celery, task: Task, timetable: TimeTable) -> str:
    schedule = crontab(**timetable.cron_dict())
    task_id = app.add_periodic_task(
        schedule, task.s(timetable.id), options={'queue': 'gen_messages'}
    )
    return task_id
