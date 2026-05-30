from zoneinfo import ZoneInfo
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

from auth import get_db, save_custom_rules, save_column_types
from connectors import DBConnector, clear_connector_cache
from validator import DataValidator
from styles import COLORS, error_card_html, get_table_style
from report_generator import show_report
from constants import (
    TABLE_STYLE_ROW_LIMIT,
    TABLE_ROW_LIMIT_MAX,
    TABLE_ROW_LIMIT_DEFAULT,
    SESSION_KEYS_TO_CLEAR_ON_REFRESH,
    AUTO_REFRESH_INTERVAL,
    AUTO_REFRESH_THRESHOLD
)

st.set_page_config(layout="wide", page_title="DataGuard Dashboard")

uid = st.session_state.user["localId"]

if "user_data_cache" not in st.session_state:
    with st.spinner("Завантаження профілю користувача..."):
        user_doc = get_db().collection("users").document(uid).get()
        if user_doc.exists:
            st.session_state.user_data_cache = user_doc.to_dict()
        else:
            st.error("Обліковий запис не знайдено в Firestore.")
            st.stop()

user_data    = st.session_state.user_data_cache
project_name = user_data.get("db_name", "Default Project")
conn_string  = user_data.get("connection_string")

if not conn_string:
    st.error("Рядок підключення до БД не знайдено.")
    st.stop()

is_mongo = conn_string.lower().startswith("mongodb")

if "user_db_connector" not in st.session_state:
    st.session_state.user_db_connector = DBConnector(conn_string)

if "table_names_cache" not in st.session_state:
    try:
        with st.spinner("Отримання списку таблиць..."):
            st.session_state.table_names_cache = st.session_state.user_db_connector.get_table_names()
    except Exception as e:
        st.error(f"Помилка підключення до БД: {e}")
        st.stop()

tables = st.session_state.table_names_cache

if "selected_table" not in st.session_state and tables:
    st.session_state.selected_table = tables[0]

if "last_auto_refresh_time" not in st.session_state:
    st.session_state.last_auto_refresh_time = time.time()

if "row_limit" not in st.session_state:
    st.session_state.row_limit = TABLE_ROW_LIMIT_DEFAULT

st.sidebar.title("DataGuard")

if st.sidebar.button("Оновити дані", use_container_width=True):
    clear_connector_cache()
    for key in SESSION_KEYS_TO_CLEAR_ON_REFRESH:
        st.session_state.pop(key, None)
    st.session_state.last_auto_refresh_time = time.time()
    st.rerun()

if st.sidebar.button("Налаштування", use_container_width=True):
    st.switch_page("views/settings_page.py")

if st.sidebar.button("Сформувати звіт", use_container_width=True):
    df_for_report = st.session_state.get("cached_df")
    if df_for_report is not None and not df_for_report.empty:
        current_active_table = st.session_state.get("selected_table", "custom_query")
        all_custom_rules     = st.session_state.user_data_cache.get("custom_rules", {})
        current_table_rules  = all_custom_rules.get(current_active_table, [])
        try:
            show_report(project_name, current_active_table, df_for_report, current_table_rules)
        except Exception as e:
            st.sidebar.error(f"Не вдалося згенерувати звіт: {e}")
    else:
        st.sidebar.error("Немає даних для формування звіту.")


def on_table_change():
    st.session_state.selected_table = st.session_state.main_table_selector
    st.session_state.pop("cached_df", None)

def on_limit_change():
    st.session_state.row_limit = st.session_state.limit_input
    st.session_state.pop("cached_df", None)

@st.fragment(run_every=AUTO_REFRESH_INTERVAL)
def render_analytics_dashboard():
    current_time = time.time()

    if current_time - st.session_state.last_auto_refresh_time >= AUTO_REFRESH_THRESHOLD:
        st.session_state.pop("cached_df", None)
        st.session_state.last_auto_refresh_time = current_time

    current_active_table = st.session_state.get(
        "selected_table",
        tables[0] if tables else "custom_query"
    )

    now = datetime.now(ZoneInfo("Europe/Kyiv"))
    st.title(f"Дашборд: {project_name} | Поточний час: {now.strftime('%H:%M:%S')}")
    st.divider()

    c_table, c_limit = st.columns([3, 1])

    if tables:
        default_index = (
            tables.index(current_active_table)
            if current_active_table in tables
            else 0
        )

        c_table.selectbox(
            "Оберіть таблицю для аналізу",
            options=tables,
            index=default_index,
            key="main_table_selector",
            on_change=on_table_change
        )

        if current_active_table not in tables:
            st.error("Недопустима таблиця")
            st.stop()

        c_limit.number_input(
            "Ліміт рядків",
            min_value=1,
            max_value=TABLE_ROW_LIMIT_MAX,
            value=st.session_state.row_limit,
            key="limit_input",
            on_change=on_limit_change
        )

        limit = st.session_state.row_limit

        clean_table  = current_active_table.replace("`", "").replace('"', "").replace("'", "")
        query_target = (
            current_active_table
            if is_mongo
            else f'SELECT * FROM "{clean_table}" LIMIT {int(limit)}'
        )

    else:
        query_label   = "Колекція" if is_mongo else "SQL запит"
        query_default = "users" if is_mongo else "SELECT * FROM users LIMIT 100"
        query_target  = c_table.text_input(query_label, query_default)
        current_active_table = "custom_query"

        c_limit.number_input(
            "Ліміт рядків",
            min_value=1,
            max_value=TABLE_ROW_LIMIT_MAX,
            value=st.session_state.row_limit,
            key="limit_input",
            on_change=on_limit_change
        )

        limit = st.session_state.row_limit

    if (
        "cached_df" not in st.session_state
        or st.session_state.get("last_query_target") != query_target
    ):
        try:
            with st.spinner("Завантаження даних з бази..."):
                st.session_state.cached_df = st.session_state.user_db_connector.fetch_data(query_target, limit=int(limit))
                st.session_state.last_query_target = query_target
        except Exception as e:
            st.error(f"Помилка при завантаженні даних: {e}")
            return

    df = st.session_state.cached_df

    all_custom_rules    = st.session_state.user_data_cache.get("custom_rules", {})
    current_table_rules = all_custom_rules.get(current_active_table, [])

    all_column_types  = st.session_state.user_data_cache.get("column_types", {})
    current_col_types = all_column_types.get(current_active_table, {})

    def local_save_rules(rules):
        save_custom_rules(current_active_table, rules)
        st.session_state.user_data_cache.setdefault("custom_rules", {})
        st.session_state.user_data_cache["custom_rules"][current_active_table] = rules

    def local_save_col_types(col_types):
        save_column_types(current_active_table, col_types)
        st.session_state.user_data_cache.setdefault("column_types", {})
        st.session_state.user_data_cache["column_types"][current_active_table] = col_types

    if df.empty:
        st.warning("Дані в цій таблиці порожні або не знайдені.")
        return


    with st.expander("Налаштування кастомних лімітів"):
        c1, c2, c3, c4 = st.columns([2.5, 1.75, 1.75, 1])

        new_col = c1.selectbox("Колонка", options=df.columns)

        saved_type  = current_col_types.get(new_col, None)
        type_locked = saved_type is not None

        if type_locked:
            c2.selectbox("Тип", ["число", "рядок"],
                        index=0 if saved_type == "число" else 1,
                        disabled=True,
                        key="col_type_locked")
            col_type = saved_type
        else:
            col_type = c2.selectbox("Тип", ["число", "рядок"], key="col_type_new")

        if col_type == "число":
            new_op  = c3.selectbox("Оператор", [">", "<", ">=", "<=", "=="])
            new_val = c4.number_input("Значення", value=0.0)
            add_btn = st.button("Додати", use_container_width=True)
        else:
            new_op  = c3.selectbox("Оператор", ["містить", "не_містить", "починається з", "регулярний вираз"])
            new_val = c4.text_input("Значення", value="")
            add_btn = st.button("Додати", use_container_width=True)

        if add_btn:
            if new_val != "" and new_val is not None:
                if not type_locked:
                    current_col_types[new_col] = col_type
                    local_save_col_types(current_col_types)

                current_rules = all_custom_rules.get(current_active_table, [])
                current_rules.append({
                    "column":   new_col,
                    "operator": new_op,
                    "value":    new_val
                })
                local_save_rules(current_rules)
                st.session_state.pop("cached_df", None)
                st.rerun(scope="fragment")

        st.divider()

        for i, rule in enumerate(list(current_table_rules)):
            r_col, r_btn = st.columns([6, 1])
            r_col.write(f"**{rule['column']}** {rule['operator']} {rule['value']}")

            if r_btn.button("Видалити", key=f"del_{i}", use_container_width=True):
                col_being_deleted = rule['column']
                current_table_rules.remove(rule)
                local_save_rules(current_table_rules)

                remaining_cols = {r['column'] for r in current_table_rules}
                if col_being_deleted not in remaining_cols:
                    current_col_types.pop(col_being_deleted, None)
                    local_save_col_types(current_col_types)

                st.session_state.pop("cached_df", None)
                st.rerun(scope="fragment")

    final_mask, stats = DataValidator.get_error_masks(df, current_table_rules, current_col_types)

    total    = df.size
    errors   = final_mask.values.sum()
    accuracy = ((total - errors) / total * 100) if total > 0 else 100

    active_errors = {label: count for label, count in stats.items() if count > 0}

    col_chart1, col_chart2, col_metrics = st.columns([2, 2, 1])

    with col_chart1:
        fig = px.pie(
            values=[total - errors, errors],
            names=["Валідні", "Аномалії"],
            hole=0.5,
            height=280,
            title="Загальна якість",
            color=["Валідні", "Аномалії"],
            color_discrete_map={
                "Валідні":  COLORS["valid"],
                "Аномалії": COLORS["invalid"]
            }
        )
        fig.update_layout(margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_chart2:
        if active_errors:
            fig2 = px.pie(
                values=list(active_errors.values()),
                names=list(active_errors.keys()),
                hole=0.5,
                height=280,
                title="Розбивка аномалій за типами"
            )
            fig2.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.success("Аномалій не виявлено!")

    with col_metrics:
        st.metric("Якість даних",      f"{accuracy:.1f}%")
        st.metric("Записів у вибірці", len(df))
        st.metric("Аномалій",          int(errors))

    st.write("### Таблиця даних")

    if len(df) <= TABLE_STYLE_ROW_LIMIT:
        st.dataframe(
            df.style.apply(get_table_style(final_mask), axis=None),
            use_container_width=True,
            height=400
        )
    else:
        st.warning("Стилізацію вимкнено (багато рядків)")
        st.dataframe(df, use_container_width=True, height=400)

    st.divider()

    with st.expander("Аналіз за типами помилок", expanded=True):
        items = list(stats.items())

        for i in range(0, len(items), 4):
            chunk = items[i:i + 4]
            cols  = st.columns(len(chunk))

            for idx, (label, count) in enumerate(chunk):
                cols[idx].markdown(error_card_html(label, count), unsafe_allow_html=True)

try:
    render_analytics_dashboard()
except Exception as e:
    st.error(f"Системна помилка під час рендерингу інтерфейсу: {e}")