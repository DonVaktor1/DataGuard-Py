import os
import sys

sys.path.append(
    os.path.abspath(
        os.path.dirname(__file__)
    )
)

import streamlit as st

st.set_page_config(
    page_title="DataGuard",
    layout="wide"
)

if st.session_state.get("user"):
    pg = st.navigation([
        st.Page("views/main_page.py", title="Дашборд", default=True),
        st.Page("views/settings_page.py", title="Налаштування")
    ], position="hidden")
else:
    pg = st.navigation([
        st.Page("views/login_page.py", title="Вхід"),
        st.Page("views/register_page.py", title="Реєстрація")
    ], position="hidden")

pg.run()