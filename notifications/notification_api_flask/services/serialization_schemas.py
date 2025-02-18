from models import User, TimeTable, Rule
from settings.extensions import ma
from marshmallow import fields
from dataclasses import dataclass
import marshmallow_dataclass
from uuid import UUID
from typing import Optional
from enum import Enum


class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User

    id = ma.auto_field()
    email = ma.auto_field()
    first_name = ma.auto_field()
    last_name = ma.auto_field()


class DumpRuleTimeTable(ma.SQLAlchemySchema):
    class Meta:
        model = TimeTable

    min = ma.auto_field()
    h = ma.auto_field()
    day = ma.auto_field()
    month = ma.auto_field()
    week_day = ma.auto_field()


class DumpRuleSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Rule

    id = ma.auto_field()
    timetable = fields.Nested(DumpRuleTimeTable)
    name = ma.auto_field()
    template = ma.auto_field()
    subject = ma.auto_field()


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


@dataclass
class Rule:
    id: Optional[UUID]
    timetable: TimeTable
    template: str
    name: str
    subject: str


class MessageType(Enum):
    EMAIL = "email"
    WEBSOCKET = "websocket"


@dataclass
class Message:
    body: str
    subject: str
    message_type: MessageType
    user_id: UUID

    def __repr__(self):
        return (
            f"Message: {self.body} to {self.user_id} " f"with type {self.message_type}"
        )


LoadRuleSchema = marshmallow_dataclass.class_schema(Rule)
MessageSchema = marshmallow_dataclass.class_schema(Message)
