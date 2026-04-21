import streamlit as st

COLORS = {
    "valid": "#00cc96",
    "invalid": "#ef553b",
    "success": "#28a745",
    "danger": "#dc3545",
    "text_muted": "#888888",
    "bg_card": "rgba(0,0,0,0.05)",
    "error_overlay": "rgba(255, 0, 0, 0.15)"
}

def error_card_html(label, count):
    color = COLORS["success"] if count == 0 else COLORS["danger"]
    return f"""
    <div style="text-align: center; padding: 10px; border-radius: 5px; background-color: {COLORS['bg_card']};">
        <p style="margin-bottom: 5px; font-size: 14px; color: {COLORS['text_muted']};">{label}</p>
        <h2 style="margin: 0; color: {color}; font-weight: bold;">{count}</h2>
    </div>
    """

def get_table_style(mask):
    def apply(data):
        style_df = data.copy()
        style_df[:] = ''
        style_df[mask] = f'background-color: {COLORS["error_overlay"]}; border: 1px solid {COLORS["danger"]};'
        return style_df
    return apply