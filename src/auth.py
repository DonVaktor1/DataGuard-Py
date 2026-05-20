import requests
import streamlit as st
import pyrebase
import json
from google.cloud import firestore
from google.oauth2 import service_account

firebase_config = st.secrets["firebase"]
firebase = pyrebase.initialize_app(dict(firebase_config))
auth = firebase.auth()

def get_db():
    if "key_file_json" in st.secrets["firebase"]:
        info = json.loads(st.secrets["firebase"]["key_file_json"])
    else:
        key_path = st.secrets["firebase"]["key_file"]
        with open(key_path, "r") as f:
            info = json.load(f)
    creds = service_account.Credentials.from_service_account_info(info)
    return firestore.Client(credentials=creds, project=info['project_id'])

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
        if "user_data_cache" in st.session_state:
            del st.session_state.user_data_cache
            
        st.context.cookies["dg_user_data"] = json.dumps(user)
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
        
        get_db().collection("users").document(uid).set({
            "email": email, 
            "connection_string": conn_string,
            "db_name": db_name,
            "custom_rules": {} 
        })
        st.session_state.user = user
        st.session_state.auth_error = None
        if "user_data_cache" in st.session_state:
            del st.session_state.user_data_cache
            
        st.context.cookies["dg_user_data"] = json.dumps(user)
    except Exception as e:
        st.session_state.auth_error = f"Помилка: {str(e)}"

def logout():
    st.session_state.user = None
    st.session_state.auth_error = None
    if "user_data_cache" in st.session_state:
        del st.session_state.user_data_cache
    if "cookies_checked" in st.session_state:
        del st.session_state.cookies_checked
        

    if "dg_user_data" in st.context.cookies:
        del st.context.cookies["dg_user_data"]

def check_auth():
    if st.session_state.get("user"):
        return True
    
    if st.session_state.get("cookies_checked"):
        return False

    saved_user = st.context.cookies.get("dg_user_data")
    st.session_state["cookies_checked"] = True
    
    if saved_user:
        try:
            user_data = json.loads(saved_user)
            st.session_state.user = user_data
            return True
        except:
            return False
    return False

def save_custom_rules(table_name, rules):
    if st.session_state.user:
        uid = st.session_state.user['localId']
        get_db().collection("users").document(uid).update({
            f"custom_rules.{table_name}": rules
        })

def delete_account():
    if not st.session_state.get("user"):
        return False
        
    try:
        uid = st.session_state.user['localId']
        id_token = st.session_state.user['idToken']
        api_key = firebase_config["apiKey"]
        
        get_db().collection("users").document(uid).delete()
        
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:delete?key={api_key}"
        payload = {"idToken": id_token}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            logout()
            return True
        else:
            st.error(f"Не вдалося видалити профіль: {response.text}")
            return False
    except Exception as e:
        st.error(f"Помилка при видаленні акаунта: {str(e)}")
        return False