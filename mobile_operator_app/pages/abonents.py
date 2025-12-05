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
        st.dataframe(df, width='stretch')
        st.caption(f"Всього записів: {len(data)}")
    else:
        st.info("База даних порожня")

except Exception as e:
    st.error(f"Помилка завантаження таблиці: {e}")


st.divider()
tab_add, tab_edit, tab_anal = st.tabs(["➕ Додати нового", "✏️ Керування", "📈 Аналітика"])
if 'edit_subscriber_ric' not in st.session_state:
    st.session_state['edit_subscriber_ric'] = ""
if 'subscriber_to_edit' not in st.session_state:
    st.session_state['subscriber_to_edit'] = None

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

with tab_edit:
    st.subheader("Пошук абонента для редагування/видалення")
    with st.form("search_for_edit_form"):
        search_ric_edit = st.text_input("Введіть RIC для пошуку:", 
                                        placeholder="RIC-...",
                                        key="search_ric_edit_input")
        
        search_button = st.form_submit_button("🔍 Знайти", type="primary")
        if search_button:
            if search_ric_edit:
                with st.spinner(f"Пошук абонента {search_ric_edit}..."):
                    found_sub = pg_db.get_subscriber(search_ric_edit)
                if found_sub:
                    st.session_state['subscriber_to_edit'] = found_sub.model_dump() 
                    st.success(f"✅ Абонента {found_sub.full_name} знайдено. Оновіть дані або видаліть нижче.")
                else:
                    st.session_state['subscriber_to_edit'] = None
                    st.error(f"Абонента з RIC '{search_ric_edit}' не знайдено.")
            else:
                st.warning("Введіть RIC для пошуку.")
    sub_data = st.session_state['subscriber_to_edit']
    if sub_data:
        st.subheader(f"Редагування даних для RIC: {sub_data['ric']}")
        st.caption("Змініть необхідні поля та натисніть 'Оновити дані'.")
        current_date = sub_data.get('contract_start_date')
        if isinstance(current_date, str):
            try:
                current_date = date.fromisoformat(current_date)
            except:
                current_date = date.today()
        last_payment_date = sub_data.get('last_payment_date')
        if isinstance(last_payment_date, str):
             try:
                last_payment_date = date.fromisoformat(last_payment_date)
             except:
                last_payment_date = date.today()
        with st.form("edit_subscriber_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**RIC:** `{sub_data['ric']}`")
                edit_name = st.text_input("ПІБ", value=sub_data['full_name'])
                edit_pin = st.text_input("PIN-код", value=sub_data['pin_code'], max_chars=4)
                all_models = ["iPhone 14", "Samsung S23", "Xiaomi 13", "Nokia 3310", "Pixel 7"]
                if sub_data['phone_model'] not in all_models:
                    all_models.append(sub_data['phone_model'])
                
                edit_model = st.selectbox("Модель телефону", 
                                          options=all_models,
                                          index=all_models.index(sub_data['phone_model'])
                                          )
                edit_active = st.checkbox("Активний контракт", value=sub_data['is_active'])
            with col2:
                all_services = ["Преміум", "Стандарт", "Економ", "Студент"]
                edit_service = st.selectbox("Тарифний план", 
                                            options=all_services,
                                            index=all_services.index(sub_data['service_type'])
                                            )
                edit_fee = st.number_input("Вартість (грн/міс)", min_value=0.0, step=10.0, value=float(sub_data['monthly_fee']))
                edit_duration = st.number_input("Тривалість контракту (міс.)", min_value=1, step=1, value=sub_data['contract_duration_months'])
                edit_date = st.date_input("Дата контракту", value=current_date)
                edit_last_payment = st.date_input("Дата останньої оплати", 
                                                  value=last_payment_date if last_payment_date else date.today()
                                                  )
            submit_edit = st.form_submit_button("💾 Оновити дані", type="secondary")
            if submit_edit:
                try:
                    updates = {
                        "full_name": edit_name,
                        "pin_code": edit_pin,
                        "phone_model": edit_model,
                        "service_type": edit_service,
                        "monthly_fee": edit_fee,
                        "contract_start_date": edit_date,
                        "contract_duration_months": edit_duration,
                        "is_active": edit_active,
                        "last_payment_date": edit_last_payment
                    }
                    pg_db.update_subscriber(sub_data['ric'], updates)
                    st.success(f"Дані абонента {sub_data['ric']} успішно оновлено!")
                    st.session_state['subscriber_to_edit'] = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Помилка при оновленні: {e}")
        if st.button("🗑️ Видалити абонента з бази", type="primary", key="delete_subscriber_btn", help="Повністю видаляє запис"):
            try:
                pg_db.delete_subscriber(sub_data['ric'])
                st.error(f"Абонента {sub_data['ric']} **повністю видалено**.")
                # Очищаємо стан, щоб прибрати дані абонента з інтерфейсу
                st.session_state['subscriber_to_edit'] = None
                st.rerun()
            except Exception as e:
                st.error(f"Помилка при видаленні: {e}")
    else:
        st.info("Введіть RIC та натисніть 'Знайти', щоб завантажити дані для керування.")
with tab_anal:
    st.subheader("Фінансова статистика")
    
    if st.button("📊 Розрахувати дохідність"):
        try:
            stats = pg_db.get_tariff_analytics()
            if stats:
                df_stats = pd.DataFrame(stats)
                
                df_stats["total_revenue"] = df_stats["total_revenue"].astype(float)
                df_stats["avg_check"] = df_stats["avg_check"].astype(float)

                c_a1, c_a2 = st.columns(2)
                with c_a1:
                    st.dataframe(df_stats, width='stretch')
                #with c_a2:
                #    st.bar_chart(df_stats, x="service_type", y="total_revenue")
            else:
                st.info("Недостатньо даних.")
        except Exception as e:
            st.error(f"Помилка аналітики: {e}")