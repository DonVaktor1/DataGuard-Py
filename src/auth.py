import streamlit as st
import pyrebase
import json
import extra_streamlit_components as cookie_controller
from google.cloud import firestore
from google.oauth2 import service_account

firebase_config = st.secrets["firebase"]
firebase = pyrebase.initialize_app(dict(firebase_config))
auth = firebase.auth()

@st.cache_resource
def get_db():
    key_path = st.secrets["firebase"]["key_file"]
    with open(key_path, "r") as f:
        info = json.load(f)
    creds = service_account.Credentials.from_service_account_info(info)
    return firestore.Client(credentials=creds, project=info['project_id'])

db = get_db()
_cookies = cookie_controller.CookieManager()

def run_login():
    email = st.session_state.get("l_email")
    password = st.session_state.get("l_pass")
    if not email or not password:
        st.session_state.auth_error = "Введіть пошту та пароль"
        return
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        st.session_state.user = user
        st.session_state.auth_error = None
        _cookies.set("dg_user_data", json.dumps(user), key="set_login")
    except:
        st.session_state.auth_error = "Невірна пошта або пароль"

def run_register():
    email = st.session_state.get("r_email")
    password = st.session_state.get("r_pass")
    confirm = st.session_state.get("r_confirm")
    conn_string = st.session_state.get("r_conn")
    db_name = st.session_state.get("r_db_name")

    if not db_name:
        st.session_state.auth_error = "Введіть назву вашої БД"
        return
    if password != confirm:
        st.session_state.auth_error = "Паролі не збігаються"
        return
    if len(password) < 6:
        st.session_state.auth_error = "Пароль має бути довше 6 символів"
        return
    try:
        auth.create_user_with_email_and_password(email, password)
        user = auth.sign_in_with_email_and_password(email, password)
        uid = user['localId']
        db.collection("users").document(uid).set({
            "email": email, 
            "connection_string": conn_string,
            "db_name": db_name 
        })
        st.session_state.user = user
        st.session_state.auth_error = None
        _cookies.set("dg_user_data", json.dumps(user), key="set_reg")
    except Exception as e:
        st.session_state.auth_error = f"Помилка: {str(e)}"

def logout():
    st.session_state.user = None
    st.session_state.auth_error = None
    _cookies.delete("dg_user_data")

def check_auth():
    if st.session_state.get("user"):
        return True
    saved_user = _cookies.get("dg_user_data")
    if saved_user:
        try:
            user_data = json.loads(saved_user)
            st.session_state.user = user_data
            return True
        except:
            return False
    return False