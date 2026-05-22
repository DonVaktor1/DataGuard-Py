import streamlit as st
from auth import run_register
from styles import COLORS

st.markdown("<div style='padding-top: 50px;'></div>", unsafe_allow_html=True)

left_space, auth_card, right_space = st.columns([1.2, 1, 1.2])

with auth_card:
    st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>DataGuard</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center; color: {COLORS['brand_gray']};'>Реєстрація проекту</h4>", unsafe_allow_html=True)

    if st.session_state.get("auth_error"):
        st.error(st.session_state.get("auth_error"))

    st.text_input("Назва проекту", key="r_db_name")
    st.text_input("Email", key="r_email")
    st.text_input("Пароль", type="password", key="r_pass")
    st.text_input("Підтвердіть пароль", type="password", key="r_confirm")
    st.text_input("Рядок підключення (URL)", key="r_conn", placeholder="postgresql://...", type="password")
    
    st.markdown("<div style='padding-top: 15px;'></div>", unsafe_allow_html=True)
    st.button("Зареєструватися", on_click=run_register, type="primary", use_container_width=True)
    
    st.divider()
    
    st.write("Вже маєте акаунт?")
    if st.button("Повернутися до входу", use_container_width=True):
        st.session_state.auth_error = None
        st.switch_page("views/login_page.py")