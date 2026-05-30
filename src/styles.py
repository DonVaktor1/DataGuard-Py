import pandas as pd

from constants import COLORS

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
        style_df = pd.DataFrame('', index=data.index, columns=data.columns)
        style_df[mask] = f'background-color: {COLORS["error_overlay"]}; border: 1px solid {COLORS["danger"]};'
        return style_df
    return apply