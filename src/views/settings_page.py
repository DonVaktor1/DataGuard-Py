import streamlit as st
from auth import logout, delete_account, db
from styles import COLORS

if "settings_updated" in st.session_state and st.session_state.settings_updated:
    st.toast(":green[Налаштування успішно оновлено!]")
    st.session_state.settings_updated = False

st.sidebar.title("DataGuard")
if st.sidebar.button("На головну", use_container_width=True):
    if "main_page_obj" in st.session_state:
        st.switch_page(st.session_state.main_page_obj)
    else:
        st.switch_page("views/main_page.py")

st.title("Налаштування")
st.divider()

try:
    uid = st.session_state.user['localId']
    if "user_data_cache" not in st.session_state:
        with st.spinner("Завантаження даних профілю..."):
            user_doc = db.collection("users").document(uid).get()
            if user_doc.exists:
                st.session_state.user_data_cache = user_doc.to_dict()
            else:
                st.error("Профіль не знайдено в базі даних.")
                st.stop()
                
    user_data = st.session_state.user_data_cache

    st.subheader("Інформація про БД")
    
    with st.form("edit_profile_form"):
        new_db_name = st.text_input("Назва проекту / БД", value=user_data.get('db_name', ''))
        new_conn_string = st.text_input("Рядок підключення (Connection String)", value=user_data.get('connection_string', ''), type="password")
        
        submit_btn = st.form_submit_button("Зберегти зміни", use_container_width=True)
        
        if submit_btn:
            if not new_db_name or not new_conn_string:
                st.toast("Усі поля повинні бути заповнені!")
            else:
                with st.spinner("Зберігаємо зміни..."):
                    try:
                        db.collection("users").document(uid).update({
                            "db_name": new_db_name,
                            "connection_string": new_conn_string
                        })
                        st.session_state.user_data_cache['db_name'] = new_db_name
                        st.session_state.user_data_cache['connection_string'] = new_conn_string
                        
                        if "db_engine" in st.session_state: del st.session_state.db_engine
                        if "cached_df" in st.session_state: del st.session_state.cached_df
                        if "table_names_cache" in st.session_state: del st.session_state.table_names_cache
                        
                        st.session_state.settings_updated = True
                        st.rerun()
                    except Exception as err:
                        st.error(f"Помилка збереження: {err}")

    st.divider()
    st.subheader("Сесія")
    st.info(f"Ви авторизовані як: **{st.session_state.user['email']}**")
    
    if st.button("Вийти з облікового запису", type="secondary", use_container_width=True):
        logout()
        st.rerun()

    st.divider()
    st.markdown(f"<h3 style='color: {COLORS['brand_red']};'>Видалення акаунта</h3>", unsafe_allow_html=True) 
    confirm_delete = st.checkbox("Я чітко усвідомлюю наслідки і хочу назавжди видалити цей акаунт")
    
    if st.button("Повністю видалити акаунт", type="primary", disabled=not confirm_delete, use_container_width=True):
        with st.spinner("Видалення профілю з системи DataGuard..."):
            if delete_account():
                st.rerun()

except Exception as e:
    st.error(f"Не вдалося завантажити сторінку налаштувань: {e}")