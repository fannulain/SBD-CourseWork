import streamlit as st
import time
import random
from datetime import date, timedelta
from databases import PostgresManager, MongoManager, RedisManager
from databases.models import Subscriber

st.set_page_config(page_title="CourseWork", layout="wide")

@st.cache_resource
def get_db_connections():
    try:
        pg = PostgresManager()
        mongo = MongoManager()
        redis = RedisManager()
        return pg, mongo, redis
    except Exception as e:
        return None, None, None, str(e)
pg_db, mongo_db, redis_db = get_db_connections()

if isinstance(pg_db, tuple) or pg_db is None:
    st.error("Не вдалося підключитися до баз даних! Перевірте Docker.")
    st.stop()
st.session_state['pg_db'] = pg_db
st.session_state['mongo_db'] = mongo_db
st.session_state['redis_db'] = redis_db

st.success("Всі бази даних підключено (Postgres, Mongo, Redis)")

def generate_test_data():
    pg_manager = st.session_state['pg_db']
    
    models = ["iPhone 13", "Samsung S21", "Xiaomi Redmi 9", "Nokia 3310", "Pixel 7"]
    names = ["Шевченко", "Бойко", "Коваль", "Мельник", "Ткаченко"]
    services = ["Преміум", "Стандарт", "Економ", "Студент"]
    
    count = 0
    errors = []

    for i in range(1, 6):
        ric = f"RIC-{random.randint(10000, 99999)}"
        try:
            subscriber = Subscriber(
                ric=ric,
                pin_code=str(random.randint(1000, 9999)),
                full_name=f"{random.choice(names)} {random.choice(names)[0]}.",
                phone_model=random.choice(models),
                phone_type="Смартфон",
                service_type=random.choice(services),
                contract_start_date=date.today() - timedelta(days=random.randint(100, 1000)),
                contract_duration_months=12,
                monthly_fee=float(random.choice([150, 250, 500])),
                is_active=random.choice([True, True, False]),
                last_payment_date=date.today() - timedelta(days=random.randint(0, 60))
            )
            pg_manager.add_subscriber(subscriber) 
            count += 1
        except Exception as e:
            errors.append(str(e))
            
    if count > 0:
        st.success(f"✅ Додано {count} нових абонентів!")
        st.balloons()
    
    if errors:
        st.error("⚠️ Помилки:")
        for e in errors: st.write(e)

def clear_all_data():
    pg_manager = st.session_state['pg_db']
    try:
        with pg_manager.connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE subscribers;")
        st.toast("Базу очищено", icon="🧹")
        time.sleep(1)
    except Exception as e:
        st.error(f"Помилка: {e}")

with st.sidebar:
    st.header("Адмінка")
    if st.button("Тестові дані"):
        generate_test_data()
        
    st.divider()
    
    if st.button("Видалити всіх", type="primary"):
        clear_all_data()
        st.rerun()