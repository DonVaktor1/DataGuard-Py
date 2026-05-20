import streamlit as st
import plotly.express as px
from datetime import datetime
import time

from auth import db, save_custom_rules
from connectors import DBConnector
from validator import DataValidator
from styles import COLORS, error_card_html, get_table_style

if "selected_table" not in st.session_state:
    st.session_state.selected_table = None

if "last_auto_refresh_time" not in st.session_state:
    st.session_state.last_auto_refresh_time = time.time()

st.sidebar.title("DataGuard")

if st.sidebar.button("Оновити дані", use_container_width=True):
    if "user_data_cache" in st.session_state: del st.session_state.user_data_cache
    if "cached_df" in st.session_state: del st.session_state.cached_df
    if "table_names_cache" in st.session_state: del st.session_state.table_names_cache
    st.session_state.last_auto_refresh_time = time.time()
    st.rerun()

if st.sidebar.button("Налаштування", use_container_width=True):
    if "settings_page_obj" in st.session_state:
        st.switch_page(st.session_state.settings_page_obj)
    else:
        st.switch_page("views/settings_page.py")

def on_table_change():
    st.session_state.selected_table = st.session_state.main_table_selector
    if "cached_df" in st.session_state: 
        del st.session_state.cached_df

try:
    uid = st.session_state.user['localId']
    
    if "user_data_cache" not in st.session_state:
        with st.spinner("Завантаження..."):
            user_doc = db.collection("users").document(uid).get()
            if user_doc.exists:
                st.session_state.user_data_cache = user_doc.to_dict()
            else:
                st.error("Обліковий запис не знайдено.")
                st.stop()

    user_data = st.session_state.user_data_cache
    project_name = user_data.get('db_name', 'Default Project')
    conn_string = user_data.get('connection_string')
    all_custom_rules = user_data.get('custom_rules', {})

    connector = DBConnector(conn_string)
    
    if "table_names_cache" not in st.session_state:
        st.session_state.table_names_cache = connector.get_table_names()
    
    tables = st.session_state.table_names_cache
    is_mongo = "mongodb" in conn_string.lower()

    @st.fragment(run_every=60)
    def render_analytics_dashboard():
        current_time = time.time()
        
        if current_time - st.session_state.last_auto_refresh_time >= 58:
            if "cached_df" in st.session_state: 
                del st.session_state.cached_df
            st.session_state.last_auto_refresh_time = current_time

        now = datetime.now()
        st.title(f"Дашборд: {project_name}  | Поточний час: {now.strftime('%H:%M:%S')}")
        st.divider()

        c_table, c_limit = st.columns([3, 1])
        if tables:
            if st.session_state.selected_table not in tables:
                st.session_state.selected_table = tables[0]
            
            default_index = tables.index(st.session_state.selected_table)

            selected_table = c_table.selectbox(
                "Оберіть таблицю для аналізу", 
                options=tables, 
                index=default_index, 
                key="main_table_selector",
                on_change=on_table_change
            )
            
            current_active_table = st.session_state.selected_table
            
            if is_mongo:
                query_target = current_active_table
            else:
                limit = c_limit.number_input("Ліміт рядків", min_value=1, max_value=10000, value=100)
                query_target = f"SELECT * FROM {current_active_table} LIMIT {limit}"
        else:
            query_label = "Колекція" if is_mongo else "SQL запит"
            query_default = "users" if is_mongo else "SELECT * FROM users LIMIT 100"
            query_target = st.text_input(query_label, query_default)
            current_active_table = "custom_query"

        if st.session_state.get('last_query_target') != query_target:
            if "cached_df" in st.session_state: del st.session_state.cached_df
            st.session_state.last_query_target = query_target

        if 'current_table_rules' not in st.session_state or st.session_state.get('last_table') != current_active_table:
            st.session_state.current_table_rules = all_custom_rules.get(current_active_table, [])
            st.session_state.last_table = current_active_table

        if "cached_df" not in st.session_state:
            st.session_state.cached_df = connector.fetch_data(query_target)

        df = st.session_state.cached_df

        def local_save_rules(rules):
            save_custom_rules(current_active_table, rules)
            if 'custom_rules' not in st.session_state.user_data_cache:
                st.session_state.user_data_cache['custom_rules'] = {}
            st.session_state.user_data_cache['custom_rules'][current_active_table] = rules

        if df.empty:
            st.warning("Дані не знайдено.")
        else:
            with st.expander("Налаштування кастомних лімітів"):
                c1, c2, c3, c4 = st.columns([2.5, 1.75, 1.75, 1])
                new_col = c1.selectbox("Колонка", options=df.columns)
                new_op = c2.selectbox("Оператор", [">", "<", ">=", "<=", "=="])
                new_val = c3.number_input("Значення", value=0.0)
            
                c4.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
                if c4.button("Додати", use_container_width=True):
                    st.session_state.current_table_rules.append({"column": new_col, "operator": new_op, "value": new_val})
                    local_save_rules(st.session_state.current_table_rules)
                    if "cached_df" in st.session_state: del st.session_state.cached_df
                    st.rerun()
            
                st.divider()
            
                for i, rule in enumerate(list(st.session_state.current_table_rules)):
                    r_col, r_btn = st.columns([6, 1])
                    r_col.write(f"**{rule['column']}** {rule['operator']} {rule['value']}")
                    
                    rule_key = f"del_{rule['column']}_{i}"
                    if r_btn.button("Видалити", key=rule_key, use_container_width=True):
                        st.session_state.current_table_rules.remove(rule)
                        local_save_rules(st.session_state.current_table_rules)
                        if "cached_df" in st.session_state: del st.session_state.cached_df
                        st.rerun()

            final_mask, stats = DataValidator.get_error_masks(df, st.session_state.current_table_rules)
            total = df.size
            errors = final_mask.values.sum()
            accuracy = ((total - errors) / total) * 100 if total > 0 else 100

            col_chart, col_metrics = st.columns([2, 1])
            with col_chart:
                fig = px.pie(values=[total - errors, errors], names=["Валідні", "Аномалії"], hole=0.5, height=280,
                            color=["Валідні", "Аномалії"], color_discrete_map={"Валідні": COLORS["valid"], "Аномалії": COLORS["invalid"]})
                fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)

            with col_metrics:
                st.metric("Якість даних", f"{accuracy:.1f}%")
                st.metric("Записів у вибірці", len(df))
                st.metric("Аномалій", int(errors))

            st.write("### Таблиця")
            styled_df = df.style.apply(get_table_style(final_mask), axis=None)
            st.dataframe(styled_df, use_container_width=True, height=400)
            st.divider()

            with st.expander("Аналіз за типами помилок", expanded=True):
                items = list(stats.items())
                max_cols = 4  
                
                for chunks in [items[i:i + max_cols] for i in range(0, len(items), max_cols)]:
                    cols = st.columns(len(chunks))
                    for idx, (label, count) in enumerate(chunks):
                        cols[idx].markdown(error_card_html(label, count), unsafe_allow_html=True)
                    st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)

    render_analytics_dashboard()

except Exception as e:
    st.error(f"Системна помилка: {e}")