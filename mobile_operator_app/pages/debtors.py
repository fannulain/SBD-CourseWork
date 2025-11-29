import streamlit as st
import pandas as pd
import time
if 'pg_db' not in st.session_state or 'redis_db' not in st.session_state:
    st.error("На головну сторінку, щоб ініціалізувати систему.")
    st.stop()
pg_db = st.session_state['pg_db']
redis_db = st.session_state['redis_db']
st.set_page_config(page_title="Боржники", page_icon="💸")
st.title("💸 Звіт по боржниках")
st.info("показує абонентів, у яких остання оплата була більше 1 місяця")
col_report, col_admin = st.columns([3, 1])

with col_report:
    st.subheader("Генерація звіту")
    
    if st.button("🔄 Згенерувати звіт", type="primary"):
        debtors = redis_db.get_cached_debtors()
        if not debtors:
            with st.spinner("Отримання даних..."):
                debtors = pg_db.get_debtors_raw() 
                redis_db.cache_debtors(debtors)
        if debtors:
            st.success("✅ Звіт успішно згенеровано.")
            data = [d.model_dump() for d in debtors]
            df = pd.DataFrame(data)
            df.rename(columns={
                'ric': 'RIC', 
                'full_name': 'ПІБ', 
                'monthly_fee': 'Тариф, грн',
                'last_payment_date': 'Остання оплата',
                'days_overdue': 'Днів простроч.',
                'debt_amount': 'Сума боргу, грн'
            }, inplace=True)
            st.dataframe(df, use_container_width=True)
            st.caption("Борг розраховано на основі місячної плати та днів прострочки.")
        else:
            st.warning("Боржників не знайдено.")

with col_admin:
    st.subheader("Керування")
    if st.button("🗑️ Очистити кеш"):
        redis_db.clear_cache()
        st.warning("Кеш очищено")