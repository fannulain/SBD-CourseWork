# tests/test_integration.py
import pytest
import time
from datetime import date
from databases.postgres_db import PostgresManager
from databases.mongo_db import MongoManager
from databases.redis_db import RedisManager
from databases.models import Subscriber, ServiceRequest


@pytest.mark.order(1)
def test_postgres_real_insert():
    print("\n\n---  TEST: PostgreSQL Integration ---")

    pg = PostgresManager()

    new_sub = Subscriber(
        ric="RIC-TEST-001",
        pin_code="1234",
        full_name="Тестовий Користувач",
        phone_model="Cyberphone 2077",
        phone_type="Смартфон",
        service_type="Преміум",
        contract_start_date=date.today(),
        contract_duration_months=24,
        monthly_fee=200.0,
        is_active=True,
        last_payment_date=date.today()
    )

    print(f" Додаємо абонента: {new_sub.full_name} ({new_sub.ric})")
    pg.add_subscriber(new_sub)

    fetched_sub = pg.get_subscriber("RIC-TEST-001")

    assert fetched_sub is not None
    assert fetched_sub.full_name == "Тестовий Користувач"
    assert fetched_sub.monthly_fee == 200.0
    print(f" Успішно зчитано з БД: {fetched_sub.full_name}")

    pg.close()

@pytest.mark.order(2)
def test_mongo_real_insert_and_delete():
    print("\n---  TEST: MongoDB Integration ---")

    mongo = MongoManager()

    req = ServiceRequest(
        ric="RIC-TEST-001",
        phone_model="Cyberphone 2077",
        issue_description="Тестова проблема: інтеграційний тест",
        status="open"
    )

    print(f" Створюємо заявку в Mongo для {req.ric}")
    req_id = mongo.create_request(req)
    print(f"   ID створеної заявки: {req_id}")

    assert req_id is not None

    found_requests = mongo.get_requests_by_ric("RIC-TEST-001")
    assert len(found_requests) > 0
    print(f" Знайдено заявок для RIC-TEST-001: {len(found_requests)}")

    print(" Видаляємо тестову заявку...")
    mongo.delete_request(req_id)


    remaining = mongo.get_requests_by_ric("RIC-TEST-001")

    assert not any(r['id'] == req_id for r in remaining)
    print(" Заявку успішно видалено з Mongo")


@pytest.mark.order(3)
def test_redis_caching():
    print("\n---  TEST: Redis Caching ---")

    pg = PostgresManager()
    redis = RedisManager()

    print(" Робимо абонента RIC-TEST-001 боржником у SQL...")
    query = "UPDATE subscribers SET last_payment_date = CURRENT_DATE - INTERVAL '2 month' WHERE ric = 'RIC-TEST-001'"
    with pg.connection.cursor() as cursor:
        cursor.execute(query)


    debtors_sql = pg.get_debtors_raw()
    assert len(debtors_sql) > 0
    print(f"   Знайдено боржників у SQL: {len(debtors_sql)}")


    print(" Записуємо в Redis...")
    redis.cache_debtors(debtors_sql)

    debtors_redis = redis.get_cached_debtors()
    print(f"   Зчитано з Redis: {len(debtors_redis)}")

    assert len(debtors_redis) == len(debtors_sql)
    assert debtors_redis[0].ric == "RIC-TEST-001"
    print(" Дані в Redis співпадають з PostgreSQL")

    redis.clear_cache()
    empty = redis.get_cached_debtors()
    assert len(empty) == 0
    print(" Кеш Redis успішно очищено")
    pg.close()