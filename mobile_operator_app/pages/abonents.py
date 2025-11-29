import streamlit as st
import pandas as pd
from datetime import date
from databases.models import Subscriber
if 'pg_db' not in st.session_state or st.session_state['pg_db'] is None:
    st.error(" На головну сторінку, щоб ініціалізувати систему.")
    st.stop()

pg_db = st.session_state['pg_db']

st.set_page_config(page_title="Абоненти", page_icon="👤", layout="wide")
c1, c2 = st.columns([5, 1])
with c1:
    st.title("👤 Управління абонентами")
with c2:
    if st.button("🔄 Оновити", type="primary"):
        st.rerun()

search_ric = st.text_input("🔍 Пошук по RIC:", placeholder="RIC-...")

try:
    if search_ric:
        found_sub = pg_db.get_subscriber(search_ric)
        data = [found_sub.model_dump()] if found_sub else []
        if not data:
            st.warning(f"Абонента з номером '{search_ric}' не знайдено.")
    else:
        subscribers = pg_db.get_all_subscribers()
        data = [s.model_dump() for s in subscribers]
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        st.caption(f"Всього записів: {len(data)}")
    else:
        st.info("База даних порожня")

except Exception as e:
    st.error(f"Помилка завантаження таблиці: {e}")


st.divider()
tab_add, tab_action, tab_anal = st.tabs(["➕ Додати нового", "⚙️ Дії з абонентом", "📈 Аналітика"])
with tab_add:
    st.subheader("Реєстрація нового абонента")
    with st.form("add_subscriber_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_ric = st.text_input("RIC", placeholder="RIC-9999")
            new_name = st.text_input("ПІБ")
            new_pin = st.text_input("PIN-код", max_chars=4)
            new_model = st.selectbox("Модель телефону", ["iPhone 14", "Samsung S23", "Xiaomi 13", "Nokia 3310", "Pixel 7"])
        
        with col2:
            new_service = st.selectbox("Тарифний план", ["Преміум", "Стандарт", "Економ", "Студент"])
            new_fee = st.number_input("Вартість (грн/міс)", min_value=0.0, step=10.0, value=150.0)
            new_date = st.date_input("Дата контракту", date.today())
            new_active = st.checkbox("Активний контракт", value=True)
        submit_add = st.form_submit_button("Зберегти абонента", type="primary")
        if submit_add:
            if new_ric and new_name and new_pin:
                try:
                    sub = Subscriber(
                        ric=new_ric, pin_code=new_pin, full_name=new_name,
                        phone_model=new_model, phone_type="Смартфон",
                        service_type=new_service, contract_start_date=new_date,
                        contract_duration_months=12, monthly_fee=new_fee,
                        is_active=new_active, last_payment_date=date.today()
                    )
                    pg_db.add_subscriber(sub) 
                    st.success(f"Абонента {new_name} успішно додано!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Помилка при додаванні: {e}")
            else:
                st.error("Заповніть обов'язкові поля (RIC, ПІБ, PIN).")
with tab_action:
    st.subheader("Керування існуючим абонентом")
    
    target_ric = st.text_input("Введіть RIC для дії:", placeholder="RIC-...")
    
    col_act1, col_act2 = st.columns(2)
    
    with col_act1:
        if st.button("⛔ Деактивувати (Відключити)", help="Змінює статус is_active на False"):
            if target_ric:
                try:
                    pg_db.deactivate_subscriber(target_ric) #
                    st.success(f"Абонента {target_ric} деактивовано.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Помилка: {e}")
            else:
                st.warning("Введіть RIC.")

    with col_act2:
        if st.button("🗑️ Видалити з бази", type="primary", help="Повністю видаляє запис"):
            if target_ric:
                try:
                    pg_db.delete_subscriber(target_ric) #
                    st.warning(f"Абонента {target_ric} видалено.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Помилка: {e}")
            else:
                st.warning("Введіть RIC.")
with tab_anal:
    st.subheader("Фінансова статистика")
    
    if st.button("📊 Розрахувати дохідність"):
        try:
            stats = pg_db.get_tariff_analytics() #
            if stats:
                df_stats = pd.DataFrame(stats)
                
                c_a1, c_a2 = st.columns(2)
                with c_a1:
                    st.dataframe(df_stats, use_container_width=True)
                with c_a2:
                    st.bar_chart(df_stats, x="service_type", y="total_revenue")
            else:
                st.info("Недостатньо даних для аналітики.")
        except Exception as e:
            st.error(f"Помилка аналітики: {e}")