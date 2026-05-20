import re
import json
import time
import urllib.parse
import requests
import streamlit as st
import pyrebase
import extra_streamlit_components as stx
from google.cloud import firestore
from google.oauth2 import service_account

firebase_config = dict(st.secrets["firebase"])
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

@st.cache_resource
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

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

def refresh_firebase_token(refresh_token):
    api_key = firebase_config["apiKey"]
    url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"
    payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code != 200:
            return None
        data = response.json()
        return {"idToken": data["id_token"], "refreshToken": data["refresh_token"]}
    except Exception as e:
        print("REFRESH ERROR:", e)
        return None

def save_user_cookie(user_data):
    try:
        encoded = urllib.parse.quote(json.dumps(user_data))
        cookie_manager.set("dg_user_data", encoded, expires_at=None, key=f"save_cookie_{time.time()}")
    except Exception as e:
        print("SAVE COOKIE ERROR:", e)

def delete_user_cookie():
    try:
        cookie_manager.delete("dg_user_data", key=f"delete_cookie_{time.time()}")
    except Exception as e:
        print("DELETE COOKIE ERROR:", e)

def run_login():
    email = st.session_state.get("l_email", "").strip()
    password = st.session_state.get("l_pass", "")
    if not email or not password:
        st.session_state.auth_error = "Введіть пошту та пароль"
        return
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        safe_user = {
            "localId": user["localId"],
            "email": user["email"],
            "idToken": user["idToken"],
            "refreshToken": user["refreshToken"]
        }
        st.session_state.user = safe_user
        st.session_state.auth_error = None
        save_user_cookie(safe_user)
        time.sleep(1)
        st.rerun()
    except Exception as e:
        print("LOGIN ERROR:", e)
        st.session_state.auth_error = "Невірна пошта або пароль"

def run_register():
    email = st.session_state.get("r_email", "").strip()
    password = st.session_state.get("r_pass", "")
    confirm = st.session_state.get("r_confirm", "")
    conn_string = st.session_state.get("r_conn", "")
    db_name = st.session_state.get("r_db_name", "").strip()
    if not db_name:
        st.session_state.auth_error = "Введіть назву вашої БД"
        return
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not email or not re.match(email_regex, email):
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
        uid = user["localId"]
        db.collection("users").document(uid).set({
            "email": email,
            "connection_string": conn_string,
            "db_name": db_name,
            "custom_rules": {}
        })
        safe_user = {
            "localId": user["localId"],
            "email": user["email"],
            "idToken": user["idToken"],
            "refreshToken": user["refreshToken"]
        }
        st.session_state.user = safe_user
        st.session_state.auth_error = None
        save_user_cookie(safe_user)
        time.sleep(1)
        st.rerun()
    except Exception as e:
        print("REGISTER ERROR:", e)
        st.session_state.auth_error = "Не вдалося створити акаунт"

def check_auth():
    if st.session_state.get("user"):
        return True
    time.sleep(0.5)
    try:
        saved_user = cookie_manager.get("dg_user_data")
    except Exception as e:
        print("COOKIE READ ERROR:", e)
        return False
    if not saved_user:
        return False
    try:
        user_data = json.loads(urllib.parse.unquote(saved_user))
        refresh_token = user_data.get("refreshToken")
        if not refresh_token:
            return False
        refreshed = refresh_firebase_token(refresh_token)
        if not refreshed:
            delete_user_cookie()
            return False
        user_data["idToken"] = refreshed["idToken"]
        user_data["refreshToken"] = refreshed["refreshToken"]
        st.session_state.user = user_data
        return True
    except Exception as e:
        print("AUTH ERROR:", e)
        delete_user_cookie()
        return False

def logout():
    st.session_state.user = None
    st.session_state.auth_error = None
    if "user_data_cache" in st.session_state:
        del st.session_state["user_data_cache"]
    delete_user_cookie()
    time.sleep(0.5)
    st.rerun()

def save_custom_rules(table_name, rules):
    if not st.session_state.get("user"):
        return
    uid = st.session_state.user["localId"]
    db.collection("users").document(uid).update({f"custom_rules.{table_name}": rules})

def delete_account():
    if not st.session_state.get("user"):
        return False
    try:
        uid = st.session_state.user["localId"]
        id_token = st.session_state.user["idToken"]
        db.collection("users").document(uid).delete()
        api_key = firebase_config["apiKey"]
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:delete?key={api_key}"
        payload = {"idToken": id_token}
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logout()
            return True
        else:
            print(response.text)
            st.error("Не вдалося видалити акаунт")
            return False
    except Exception as e:
        print("DELETE ACCOUNT ERROR:", e)
        st.error("Помилка при видаленні акаунта")
        return False