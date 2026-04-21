import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from auth import run_login, run_register, logout, db, check_auth
from connectors import DBConnector
from validator import DataValidator
from styles import COLORS, error_card_html


st.set_page_config(page_title="DataGuard Cloud", layout="wide")

if 'user' not in st.session_state:
    st.session_state.user = None

if 'auth_error' not in st.session_state:
    st.session_state.auth_error = None

check_auth()

if not st.session_state.user:

    st.title("DataGuard Cloud")

    if st.session_state.auth_error:
        st.error(st.session_state.auth_error)

    tab1, tab2 = st.tabs(["Вхід", "Реєстрація"])

    with tab1:
        st.text_input("Email", key="l_email")
        st.text_input("Пароль", type="password", key="l_pass")
        st.button("Увійти", on_click=run_login, type="primary", use_container_width=True)

    with tab2:
        st.text_input("Назва проекту", key="r_db_name")
        st.text_input("Email", key="r_email")
        st.text_input("Пароль", type="password", key="r_pass")
        st.text_input("Підтвердіть пароль", type="password", key="r_confirm")
        st.text_input("Рядок підключення", key="r_conn")
        st.button("Створити акаунт", on_click=run_register, type="primary", use_container_width=True)

else:
    st.sidebar.title("DataGuard")

    if st.sidebar.button("Оновити дані", use_container_width=True):
        st.rerun()

    try:
        uid = st.session_state.user['localId']
        user_doc = db.collection("users").document(uid).get()

        if user_doc.exists:

            user_data = user_doc.to_dict()
            project_name = user_data.get('db_name', 'Default Project')
            conn_string = user_data.get('connection_string')

            header_placeholder = st.empty()

            st.divider()

            is_mongo = "mongodb" in conn_string.lower()
            query_label = "Колекція" if is_mongo else "SQL запит"
            query_default = "users" if is_mongo else "SELECT * FROM users LIMIT 100"

            query_target = st.text_input(query_label, query_default)

            @st.fragment(run_every=60)
            def render_dashboard():
                now = datetime.now()

                header_placeholder.title(
                    f"Дашборд: {project_name}  | Поточний час: {now.strftime('%H:%M:%S')}"
                )

                try:
                    connector = DBConnector(conn_string)
                    df = connector.fetch_data(query_target)

                    if df.empty:
                        st.warning("Дані не знайдено.")
                        return
                    
                    final_mask, stats = DataValidator.get_error_masks(df)

                    total = df.size
                    errors = final_mask.values.sum()
                    accuracy = ((total - errors) / total) * 100

                    col_chart, col_metrics = st.columns([2, 1])

                    with col_chart:
                        fig = px.pie(
                            values=[total - errors, errors],
                            names=["Валідні", "Аномалії"],
                            hole=0.5,
                            height=280,
                            color=["Валідні", "Аномалії"],
                            color_discrete_map={
                                "Валідні": COLORS["valid"],
                                "Аномалії": COLORS["invalid"]
                            }
                        )
                        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                        st.plotly_chart(fig, use_container_width=True)

                    with col_metrics:
                        st.metric("Якість даних", f"{accuracy:.1f}%")
                        st.metric("Записів у вибірці", len(df))
                        st.metric("Аномалій", errors)

                    st.write("### Таблиця аномалій")

                    styled_df = df.style.apply(lambda d: pd.DataFrame(
                        [[
                            f'background-color: {COLORS["error_overlay"]}; border: 1px solid {COLORS["danger"]}'
                            if final_mask.iloc[r, c] else ''
                            for c in range(len(d.columns))
                        ] for r in range(len(d))],
                        index=d.index,
                        columns=d.columns
                    ), axis=None)

                    st.dataframe(styled_df, use_container_width=True, height=400)

                    st.divider()

                    with st.expander("🔍 Аналіз за типами помилок", expanded=True):
                        cols = st.columns(len(stats))
                        for i, (label, count) in enumerate(stats.items()):
                            cols[i].markdown(
                                error_card_html(label, count),
                                unsafe_allow_html=True
                            )

                except Exception as e:
                    st.error(f"Помилка даних: {e}")

            render_dashboard()

            st.sidebar.markdown("<br>" * 10, unsafe_allow_html=True)
            st.sidebar.divider()
            st.sidebar.write(f"{st.session_state.user['email']}")
            st.sidebar.button("Вийти", on_click=logout, use_container_width=True)

        else:
            st.error("Обліковий запис не знайдено.")

    except Exception as e:
        st.error(f"Системна помилка: {e}")