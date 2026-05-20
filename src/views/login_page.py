import streamlit as st
from auth import run_login
from styles import COLORS

st.markdown("<div style='padding-top: 80px;'></div>", unsafe_allow_html=True)

left_space, auth_card, right_space = st.columns([1.2, 1, 1.2])

with auth_card:
    st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>DataGuard</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center; color: {COLORS['brand_gray']};'>Вхід у систему</h4>", unsafe_allow_html=True)

    if st.session_state.auth_error:
        st.error(st.session_state.auth_error)

    st.text_input("Email", key="l_email")
    st.text_input("Пароль", type="password", key="l_pass")
    
    st.markdown("<div style='padding-top: 15px;'></div>", unsafe_allow_html=True)
    st.button("Увійти", on_click=run_login, type="primary", use_container_width=True)
    
    st.divider()
    
    st.write("Немає облікового запису?")
    if st.button("Створити новий акаунт", use_container_width=True):
        st.session_state.auth_error = None
        st.switch_page("views/register_page.py")