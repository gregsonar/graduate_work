import uuid
from typing import Tuple

from psycopg2.extras import _connection


def clear_test_data(test_data: Tuple[str], db_connection: _connection):
    with db_connection.cursor() as cursor:
        query = "DELETE FROM RULE WHERE RULE.name in %s"
        params = (test_data,)
        cursor.execute(query, params)
        query = "DELETE FROM timetable WHERE id in (select timetable_id from RULE where RULE.name in %s)"
        params = (test_data,)
        cursor.execute(query, params)
        db_connection.commit()


def get_valid_user_id(connection: _connection) -> str:
    user_id = uuid.uuid4()
    with connection.cursor() as cursor:
        query = "SELECT id FROM USERS LIMIT 1"
        cursor.execute(query)
        for row in cursor:
            user_id = row[0]
    return str(user_id)
