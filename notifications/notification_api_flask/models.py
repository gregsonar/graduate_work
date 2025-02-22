import datetime
import enum
import uuid

from sqlalchemy.dialects.postgresql import UUID

from settings.extensions import db


class Roles(enum.Enum):
    user = "user"
    privileged_user = "privileged_user"
    admin = "admin"


class User(db.Model):
    __bind_key__ = "auth_sql"
    __tablename__ = "users"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), nullable=False, unique=True)

    def __repr__(self) -> str:
        return f"<id {self.id}>"


class TimeTable(db.Model):
    __bind_key__ = "rule_sql"
    __tablename__ = "timetable"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = db.Column(db.String, nullable=False)
    min = db.Column(db.INTEGER)
    h = db.Column(db.INTEGER)
    day = db.Column(db.INTEGER)
    month = db.Column(db.INTEGER)
    week_day = db.Column(db.INTEGER)

    rules = db.relationship("Rule", backref="timetable")

    def __repr__(self) -> str:
        return f"<m {self.min}, h {self.h}, d {self.day}, m {self.month}, w {self.week_day}>"


class Rule(db.Model):
    __bind_key__ = "rule_sql"
    __tablename__ = "rule"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False, unique=True)
    template = db.Column(db.String(2047), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    timetable_id = db.Column(UUID(as_uuid=True), db.ForeignKey("timetable.id"))

    def __repr__(self) -> str:
        return f"<id {self.id} time {self.timetable}>"
