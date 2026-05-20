import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import streamlit as st
from auth import check_auth

st.set_page_config(page_title="DataGuard", layout="wide")

if 'user' not in st.session_state:
    st.session_state.user = None

if 'auth_error' not in st.session_state:
    st.session_state.auth_error = None

check_auth()

if not st.session_state.user:
    login_page = st.Page("src/views/login_page.py", title="Вхід")
    register_page = st.Page("src/views/register_page.py", title="Реєстрація")
    pg = st.navigation([login_page, register_page], position="hidden")
else:
    main_page = st.Page(
        "src/views/main_page.py", 
        title="Дашборд", 
        default=True 
    )
    settings_page = st.Page(
        "src/views/settings_page.py", 
        title="Налаштування", 
    )

    st.session_state.main_page_obj = main_page
    st.session_state.settings_page_obj = settings_page
    
    pg = st.navigation([main_page, settings_page], position="hidden")

pg.run()