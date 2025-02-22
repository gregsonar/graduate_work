import uuid
from http import HTTPStatus
import requests


def test_send_email_message_wrong_user(email_message: dict, message_url: str, clear_db):
    email_message["user_id"] = str(uuid.uuid4())
    resp = requests.post(message_url, json=email_message)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_send_email(email_message: dict, message_url: str, clear_db):
    resp = requests.post(message_url, json=email_message)
    assert resp.status_code == HTTPStatus.OK
