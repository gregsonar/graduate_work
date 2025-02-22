from http import HTTPStatus
import requests


def test_add(rule_test_1: dict, rule_url: str, clear_db):
    resp = _add_rule(rule_test_1, rule_url)
    assert resp.status_code == HTTPStatus.CREATED

    resp_data = resp.json()
    for key in rule_test_1.keys():
        if key == "id":
            continue
        assert resp_data[key] == rule_test_1[key]


def test_add_conflict(rule_test_1: dict, rule_url: str, clear_db):
    resp = _add_rule(rule_test_1, rule_url)
    assert resp.status_code == HTTPStatus.CREATED

    resp = _add_rule(rule_test_1, rule_url)
    assert resp.status_code == HTTPStatus.CONFLICT


def test_del_no_rule(rule_test_1: dict, rule_url: str, clear_db):
    resp = _del_rule(rule_test_1.get("name"), rule_url)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_del(rule_test_1: dict, rule_url: str, clear_db):
    _add_rule(rule_test_1, rule_url)
    resp = _del_rule(rule_test_1.get("name"), rule_url)
    assert resp.status_code == HTTPStatus.OK


def test_update_no_rule(rule_test_1: dict, rule_url: str, clear_db):
    resp = _update_rule(rule_test_1, rule_url)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_update_no_rule(rule_test_1: dict, rule_url: str, clear_db):
    resp = _add_rule(rule_test_1, rule_url)
    assert resp.status_code == HTTPStatus.CREATED

    resp = _update_rule(rule_test_1, rule_url)
    assert resp.status_code == HTTPStatus.OK


def _update_rule(rule: dict, rule_url: str) -> requests.Response:
    return requests.patch(rule_url, json=rule)


def _del_rule(rule_name: str, rule_url: str) -> requests.Response:
    return requests.delete(rule_url, json={"name": rule_name})


def _add_rule(rule: dict, rule_url: str) -> requests.Response:
    return requests.post(rule_url, json=rule)
