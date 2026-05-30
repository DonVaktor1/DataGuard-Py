import re
import json
import requests
import streamlit as st
import pyrebase
from google.cloud import firestore
from google.oauth2 import service_account

from constants import EMAIL_REGEX, SESSION_KEYS_TO_CLEAR_ON_LOGOUT

firebase_config = dict(st.secrets["firebase"])
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

@st.cache_resource
def get_db():
    if "key_file_json" in st.secrets["firebase"]:
        info = json.loads(st.secrets["firebase"]["key_file_json"])
    else:
        key_path = st.secrets["firebase"]["key_file"]
        with open(key_path, "r") as f:
            info = json.load(f)
    creds = service_account.Credentials.from_service_account_info(info)
    return firestore.Client(credentials=creds, project=info["project_id"])

db = get_db()

def run_login():
    email    = st.session_state.get("l_email", "").strip()
    password = st.session_state.get("l_pass", "")

    if not email or not password:
        st.session_state.auth_error = "Введіть пошту та пароль"
        return

    try:
        user = auth.sign_in_with_email_and_password(email, password)
    except Exception:
        st.session_state.auth_error = "Невірна пошта або пароль"
        return

    _finalize_auth(user)

def run_register():
    email       = st.session_state.get("r_email", "").strip()
    password    = st.session_state.get("r_pass", "")
    confirm     = st.session_state.get("r_confirm", "")
    conn_string = st.session_state.get("r_conn", "")
    db_name     = st.session_state.get("r_db_name", "").strip()
    

    if not db_name:
        st.session_state.auth_error = "Введіть назву вашої БД"
        return

    if not email or not re.match(EMAIL_REGEX, email):
        st.session_state.auth_error = "Введіть коректну пошту"
        return

    if password != confirm:
        st.session_state.auth_error = "Паролі не збігаються"
        return

    if len(password) < 6:
        st.session_state.auth_error = "Пароль мінімум 6 символів"
        return

    try:
        auth.create_user_with_email_and_password(email, password)
        user = auth.sign_in_with_email_and_password(email, password)
        uid  = user["localId"]

        db.collection("users").document(uid).set({
            "email": email,
            "connection_string": conn_string,
            "db_name": db_name,
            "custom_rules": {},
            "column_types": {}
        })
    except Exception:
        st.session_state.auth_error = "Не вдалося створити акаунт"
        return

    _finalize_auth(user)

def _finalize_auth(user):
    safe_user = {
        "localId":      user["localId"],
        "email":        user["email"],
        "idToken":      user["idToken"],
        "refreshToken": user["refreshToken"]
    }
    st.session_state.user             = safe_user
    st.session_state.auth_error       = None
    st.session_state.is_authenticated = True

def logout():
    for key in SESSION_KEYS_TO_CLEAR_ON_LOGOUT:
        st.session_state.pop(key, None)
    st.session_state.logged_out = True
    st.rerun()

def save_custom_rules(table_name, rules):
    if not st.session_state.get("user"):
        return
    uid = st.session_state.user["localId"]
    db.collection("users").document(uid).update({
        f"custom_rules.{table_name}": rules
    })
    
def save_column_types(table_name, column_types):
    if not st.session_state.get("user"):
        return
    uid = st.session_state.user["localId"]
    db.collection("users").document(uid).update({
        f"column_types.{table_name}": column_types
    })

def delete_account():
    if not st.session_state.get("user"):
        return False
    try:
        uid      = st.session_state.user["localId"]
        id_token = st.session_state.user["idToken"]

        db.collection("users").document(uid).delete()

        api_key  = firebase_config["apiKey"]
        url      = f"https://identitytoolkit.googleapis.com/v1/accounts:delete?key={api_key}"
        response = requests.post(url, json={"idToken": id_token}, timeout=10)

        if response.status_code == 200:
            logout()
            return True
        return False
    except Exception:
        return False