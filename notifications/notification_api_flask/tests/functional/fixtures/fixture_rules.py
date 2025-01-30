from pytest import fixture
from typing import Tuple


@fixture
def rules_names(rule_test_1, rule_test_2, rule_test_3) -> Tuple[str]:
    return (
        rule_test_1.get('name'),
        rule_test_2.get('name'),
        rule_test_3.get('name'),
    )


@fixture
def rule_test_1():
    return {
        'id': 'e4dcce5a-b6cb-48fd-9e54-fd757858bcb0',
        'name': 'test1',
        'template': 'dddd',
        'subject': 'ffff',
        'timetable': {'day': 1, 'h': 0, 'min': 0, 'month': 0, 'week_day': 0},
    }


@fixture
def rule_test_2():
    return {
        'id': '4e940848-640a-4e22-9284-df694034596e',
        'name': 'test2',
        'template': 'dddd',
        'subject': 'ffff',
        'timetable': {'day': 1, 'h': 0, 'min': 0, 'month': 0, 'week_day': 0},
    }


@fixture
def rule_test_3():
    return {
        'id': '4afa73a6-2f51-4ac1-9bc9-452f812c9f30',
        'name': 'test3',
        'template': 'dddd',
        'subject': 'ffff',
        'timetable': {'day': 1, 'h': 0, 'min': 0, 'month': 0, 'week_day': 0},
    }
