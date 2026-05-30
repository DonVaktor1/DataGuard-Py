COLORS = {
    "brand_red": "#ff4b4b",
    "brand_gray": "#888888",
    "valid": "#00cc96",
    "invalid": "#ef553b",
    "success": "#28a745",
    "danger": "#dc3545",
    "text_muted": "#888888",
    "bg_card": "rgba(0,0,0,0.05)",
    "error_overlay": "rgba(255, 0, 0, 0.15)",
}

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
PHONE_REGEX = r'^\+380\d{9}$'

TABLE_STYLE_ROW_LIMIT = 5000
TABLE_ROW_LIMIT_MAX = 10000
TABLE_ROW_LIMIT_DEFAULT = 100

SESSION_KEYS_TO_CLEAR_ON_REFRESH = [
    "user_data_cache",
    "cached_df",
    "table_names_cache",
    "user_db_connector",
    "last_query_target"
]

SESSION_KEYS_TO_CLEAR_ON_LOGOUT = [
    "user",
    "user_data_cache",
    "selected_table",  
    "cached_df",
    "table_names_cache",
    "user_db_connector",
    "last_query_target",
    "logged_out"
]

AUTO_REFRESH_INTERVAL = 60      
AUTO_REFRESH_THRESHOLD = 58      