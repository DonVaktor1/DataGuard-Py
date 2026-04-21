import pandas as pd

class DataValidator:
    EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE_REGEX = r'^\+380\d{9}$'

    @staticmethod
    def get_error_masks(df):
        null_mask = df.isna() | df.applymap(lambda x: str(x).strip().lower() in ["", "none", "nan", "null"])
        numeric_df = df.apply(pd.to_numeric, errors='coerce')
        negative_mask = (numeric_df < 0).fillna(False)
        email_mask = pd.DataFrame(False, index=df.index, columns=df.columns)
        phone_mask = pd.DataFrame(False, index=df.index, columns=df.columns)
        date_mask = pd.DataFrame(False, index=df.index, columns=df.columns)

        for col in df.columns:
            col_l = col.lower()
            col_str = df[col].astype(str).str.strip()
            
            if any(x in col_l for x in ["email", "mail"]):
                email_mask[col] = ~col_str.str.match(DataValidator.EMAIL_REGEX) & ~null_mask[col]
            if any(x in col_l for x in ["phone", "tel"]):
                phone_mask[col] = ~col_str.str.match(DataValidator.PHONE_REGEX) & ~null_mask[col]
            if any(x in col_l for x in ["date", "time"]):
                date_mask[col] = pd.to_datetime(df[col], errors='coerce').isna() & ~null_mask[col]

        final_mask = null_mask | negative_mask | date_mask | email_mask | phone_mask
        
        stats = {
            "Порожні (NULL)": null_mask.values.sum(),
            "Email": email_mask.values.sum(),
            "Телефон": phone_mask.values.sum(),
            "Дата": date_mask.values.sum(),
            "Числа < 0": negative_mask.values.sum()
        }
        return final_mask, stats