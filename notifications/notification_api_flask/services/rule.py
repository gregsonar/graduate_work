from typing import List

from sqlalchemy.orm import Session

from models import TimeTable as DatabaseTimeTable, Rule as DatabaseRule
from .serialization_schemas import TimeTable, Rule
from settings.extensions import db, logger


class RuleExists(Exception):
    pass


class RuleNotFound(Exception):
    pass


def add_message_rule(rule: Rule) -> DatabaseRule:
    db_rule = DatabaseRule.query.filter_by(name=rule.name).first()
    if db_rule is not None:
        raise RuleExists

    timetable = _get_timetable(rule.timetable, db.session)

    db_rule = DatabaseRule(
        name=rule.name,
        template=rule.template,
        timetable=timetable,
        subject=rule.subject,
    )

    db.session.add(db_rule)
    db.session.commit()

    return db_rule


def update_message_rule(rule: Rule) -> DatabaseRule:

    db_rule = rule_data(rule.name)
    timetable = _get_timetable(rule.timetable, db.session)

    db_rule.template = rule.template
    db_rule.timetable = timetable
    db_rule.subject = rule.subject
    db.session.add(db_rule)
    db.session.commit()

    return db_rule


def delete_message_rule(name: str):
    db_rule = rule_data(name)
    db.session.delete(db_rule)
    db.session.commit()


def rule_data(name) -> DatabaseRule:
    db_rule = DatabaseRule.query.filter_by(name=name).first()
    if db_rule is None:
        raise RuleNotFound
    return db_rule


def get_all_rules() -> List[DatabaseRule]:
    return DatabaseRule.query.all()


def _get_timetable(
    timetable_data: TimeTable, session: Session
) -> DatabaseTimeTable:

    timetable = DatabaseTimeTable.query.filter_by(
        min=timetable_data.min,
        h=timetable_data.h,
        day=timetable_data.day,
        month=timetable_data.month,
        week_day=timetable_data.week_day,
    ).first()

    if timetable is None:
        logger.info('Creating new time record %s', timetable_data)
        timetable = DatabaseTimeTable(
            key=timetable_data.key,
            min=timetable_data.min,
            h=timetable_data.h,
            day=timetable_data.day,
            month=timetable_data.month,
            week_day=timetable_data.week_day,
        )
        session.add(timetable)
    return timetable
