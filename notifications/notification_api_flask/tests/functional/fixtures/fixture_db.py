from functional.utils.db import clear_test_data
from psycopg2 import connect
from psycopg2.extras import _connection
from pytest import fixture


@fixture
def db_connection(config) -> _connection:
    with connect(**config.db_config.get_dns()) as connection:
        yield connection


@fixture
def auth_db_connection(config) -> _connection:
    with connect(**config.auth_db_config.get_dns()) as connection:
        yield connection


@fixture
def clear_db(rules_names, db_connection):
    clear_test_data(rules_names, db_connection)
