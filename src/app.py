import os
import sys

sys.path.append(
    os.path.abspath(
        os.path.dirname(__file__)
    )
)

import streamlit as st

from auth import init_auth

st.set_page_config(
    page_title="DataGuard",
    layout="wide"
)

init_auth()

if not st.session_state.auth_checked:
    st.stop()

if st.session_state.is_authenticated:
    pg = st.navigation([
        st.Page(
            "views/main_page.py",
            title="Дашборд",
            default=True
        ),

        st.Page(
            "views/settings_page.py",
            title="Налаштування"
        )
    ], position="hidden")

else:
    pg = st.navigation([
        st.Page(
            "views/login_page.py",
            title="Вхід"
        ),

        st.Page(
            "views/register_page.py",
            title="Реєстрація"
        )
    ], position="hidden")

pg.run()