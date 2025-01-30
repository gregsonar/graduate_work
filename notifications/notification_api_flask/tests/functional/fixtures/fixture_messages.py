from pytest import fixture

from functional.utils.db import get_valid_user_id


@fixture
def email_message(valid_user_id) -> dict:
    return {
        'body': 'test',
        'subject': 'test',
        'message_type': 'EMAIL',
        'user_id': valid_user_id,
    }


@fixture
def valid_user_id(auth_db_connection):
    return get_valid_user_id(auth_db_connection)
