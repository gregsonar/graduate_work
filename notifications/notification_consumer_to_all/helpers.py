from functools import wraps

import psycopg2
from psycopg2.extras import DictCursor

from config import dsl_for_users_data


def psycopg2_cursor_fetch_users(func):
    @wraps(func)
    def inner(*args, **kwargs):
        with psycopg2.connect(**dsl_for_users_data) as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            fn = func(cursor=cur, *args, **kwargs)
        return fn

    return inner
