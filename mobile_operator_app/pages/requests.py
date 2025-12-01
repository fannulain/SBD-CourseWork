import streamlit as st
import pandas as pd
from databases.models import ServiceRequest
from typing import List, Dict, Any
if 'mongo_db' not in st.session_state:
    st.error("На головну сторінку, щоб ініціалізувати систему.")
    st.stop()
mongo_db = st.session_state['mongo_db']
st.set_page_config(page_title="Заявки", page_icon="🛠", layout="wide")

st.title("🛠 Сервісні заявки")
tab_create, tab_active, tab_search = st.tabs(["📝 Нова заявка", "📋 Активні (В роботі)", "🔍 Пошук та Історія"])
with tab_create:
    st.subheader("Реєстрація звернення")
    with st.form("create_ticket"):
        c1, c2 = st.columns(2)
        with c1:
            new_ric = st.text_input("RIC клієнта", placeholder="RIC-1001")
            new_model = st.selectbox("Пристрій", ["iPhone 14", "Samsung S23", "Xiaomi", "Інше"])
        with c2:
            new_type = st.selectbox("Тип проблеми", ["Ремонт", "Зв'язок", "Консультація"])
            new_desc = st.text_area("Опис ситуації")
        if st.form_submit_button("✅ Створити заявку", type="primary"):
            if new_ric and new_desc:
                try:
                    req = ServiceRequest(
                        ric=new_ric,
                        phone_model=new_model,
                        issue_description=f"[{new_type}] {new_desc}"
                    )
                    #
                    tid = mongo_db.create_request(req)
                    st.success(f"Заявку створено! ID: {tid}")
                except Exception as e:
                    st.error(f"Помилка: {e}")
            else:
                st.warning("Введіть RIC та опис.")
with tab_active:
    st.subheader("Черга заявок")
    
    if st.button("🔄 Оновити список"):
        st.rerun()
    active_requests = mongo_db.get_all_requests(only_open=True)
    if not active_requests:
        st.info("Черга пуста")
    else:
        for req in active_requests:
            with st.container(border=True):
                col_info, col_actions = st.columns([4, 1])
                with col_info:
                    st.markdown(f"**RIC:** `{req['ric']}` | **Пристрій:** {req['phone_model']}")
                    st.write(f"📝 {req['issue_description']}")
                    st.caption(f"ID: {req['id']} | Створено: {req['created_at']}")
                with col_actions:
                    if st.button("✅ Закрити", key=f"close_{req['id']}"):
                        mongo_db.close_request(req['id'])
                        st.toast("Заявку перенесено в архів")
                        st.rerun()
                    if st.button("🗑️ Видалити", key=f"del_{req['id']}"):
                        mongo_db.delete_request(req['id'])
                        st.toast("Заявку видалено")
                        st.rerun()
with tab_search:
    st.subheader("Історія обслуговування")
    
    search_ric = st.text_input("Введіть RIC для пошуку:", placeholder="RIC-...")
    
    if search_ric:
        results = mongo_db.get_requests_by_ric(search_ric) 
        if results:
            st.write(f"Знайдено записів: {len(results)}")
            for res in results:
                status_color = "🟢" if res['status'] == 'open' else "🔴"
                date_str = res.get('created_at', '')
                desc_str = res.get('issue_description', 'Без опису')
                with st.expander(f"{status_color} {date_str} | {desc_str}"):
                    col_det1, col_det2 = st.columns(2)
                    with col_det1:
                        st.write(f"**RIC:** `{res.get('ric', '-')}`")
                        st.write(f"**Модель:** {res.get('phone_model', '-')}")
                    with col_det2:
                        st.write(f"**Статус:** {res.get('status', '-')}")
                        if res.get('closed_at'):
                            st.write(f"**Закрито:** {res['closed_at']}")
                    st.caption(f"Технічний ID: {res['id']}")
                    if st.button("❌ Видалити запис", key=f"hist_del_{res['id']}"):
                        mongo_db.delete_request(res['id'])
                        st.warning("Запис видалено.")
                        st.rerun()
        else:
            st.warning("Історії не знайдено.")