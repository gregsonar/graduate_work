import uuid
from dataclasses import dataclass
from typing import Generator, Optional
from uuid import UUID

import psycopg2
from notification_scheduler.settings.config import AUTH_DSL


class TemplateDataGetter:
    def __init__(self):
        pass

    def template_data(self) -> Generator["TemplateData", None, None]:
        with psycopg2.connect(**AUTH_DSL) as conn, conn.cursor() as cursor:
            query = f"SELECT id, first_name, last_name, email  FROM users"
            cursor.execute(query)
            data = [el for el in cursor]
        for el in data:
            yield TemplateData(
                user=User(id=el[0], first_name=el[1], last_name=el[2], email=el[3])
            )


@dataclass
class User:
    id: Optional[uuid.UUID]
    first_name: str
    last_name: str
    email: str

    def to_dict(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
        }


@dataclass
class TemplateData:
    user: User

    def render_data(self) -> dict:
        return self.user.to_dict()


@dataclass
class TimeTable:
    id: Optional[UUID]
    min: int
    h: int
    day: int
    month: int
    week_day: int

    @property
    def key(self) -> str:
        return f"m{self.min}h{self.h}d{self.day}m{self.month}w{self.week_day}"

    def cron_dict(self) -> dict:
        return {
            "minute": cron_data(self.min),
            "hour": cron_data(self.h),
            "day_of_week": cron_data(self.week_day),
            "month_of_year": cron_data(self.month),
        }


def cron_data(val):
    return val if val != 0 else "*"
