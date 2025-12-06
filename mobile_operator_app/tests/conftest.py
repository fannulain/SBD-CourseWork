# tests/conftest.py
import pytest
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

TEST_PG_DB = "mobile_operator_test_db"
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    1. Підключається до Postgres (системної БД).
    2. Створює окрему БД 'mobile_operator_test_db' для тестів.
    3. Підміняє змінну оточення PG_DB, щоб PostgresManager підключався саме до неї.
    4. Після тестів — видаляє цю базу.
    """
    print(f"\n[SETUP] Створення тестової БД: {TEST_PG_DB}...")

    con = psycopg2.connect(
        dbname="postgres", user=PG_USER, password=PG_PASSWORD, host=PG_HOST, port=PG_PORT
    )
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = con.cursor()

    cursor.execute(f"DROP DATABASE IF EXISTS {TEST_PG_DB};")
    cursor.execute(f"CREATE DATABASE {TEST_PG_DB};")
    cursor.close()
    con.close()

    os.environ["PG_DB"] = TEST_PG_DB

    yield

    print(f"\n[TEARDOWN]  Видалення тестової БД: {TEST_PG_DB}...")

    con = psycopg2.connect(
        dbname="postgres", user=PG_USER, password=PG_PASSWORD, host=PG_HOST, port=PG_PORT
    )
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = con.cursor()

    cursor.execute(f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{TEST_PG_DB}'
        AND pid <> pg_backend_pid();
    """)
    cursor.execute(f"DROP DATABASE {TEST_PG_DB};")
    cursor.close()
    con.close()