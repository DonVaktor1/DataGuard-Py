import pandas as pd
import numpy as np

class DataValidator:
    EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE_REGEX = r'^\+380\d{9}$'

    @staticmethod
    def get_error_masks(df, custom_rules=[]):
        null_mask = df.isna()
        
        if df.empty:
            return null_mask, {k: 0 for k in ["Порожні (NULL)", "Email", "Телефон", "Дата/Час", "Числа < 0", "Аномалії віку", "Порушення лімітів", "Дублікати рядків"]}

        string_df = df.astype(str).apply(lambda x: x.str.strip().str.lower())
        null_mask = null_mask | string_df.isin(["", "none", "nan", "null"])
        
        numeric_df = df.apply(pd.to_numeric, errors='coerce')
        negative_mask = (numeric_df < 0).fillna(False)
        
        email_mask = pd.DataFrame(False, index=df.index, columns=df.columns)
        phone_mask = pd.DataFrame(False, index=df.index, columns=df.columns)
        date_mask = pd.DataFrame(False, index=df.index, columns=df.columns)
        business_rules_mask = pd.DataFrame(False, index=df.index, columns=df.columns)
        custom_rules_mask = pd.DataFrame(False, index=df.index, columns=df.columns)
        
        duplicate_rows_mask = df.duplicated(keep=False)
        
        for col in df.columns:
            col_l = col.lower()
            col_str = string_df[col] # беремо вже готовий очищений стовпчик
            
            if any(x in col_l for x in ["email", "mail"]):
                email_mask[col] = ~col_str.str.match(DataValidator.EMAIL_REGEX) & ~null_mask[col]
            
            if any(x in col_l for x in ["phone", "tel"]):
                phone_mask[col] = ~col_str.str.match(DataValidator.PHONE_REGEX) & ~null_mask[col]
            
            if any(x in col_l for x in ["date", "time"]):
                date_mask[col] = pd.to_datetime(df[col], errors='coerce').isna() & ~null_mask[col]
            
            if "age" in col_l or "вік" in col_l:
                business_rules_mask[col] = ((numeric_df[col] < 0) | (numeric_df[col] > 120)) & ~null_mask[col]

        for rule in custom_rules:
            col = rule.get('column')
            if col in df.columns:
                op = rule.get('operator')
                limit = rule.get('value')
                val = numeric_df[col]
                
                if op == ">":    m = (val <= limit)
                elif op == "<":  m = (val >= limit)
                elif op == ">=": m = (val < limit)
                elif op == "<=": m = (val > limit)
                elif op == "==": m = (val != limit)
                else: continue
                
                custom_rules_mask[col] = custom_rules_mask[col] | (m & ~null_mask[col]).fillna(False)

        final_mask = (
            null_mask | negative_mask | date_mask | 
            email_mask | phone_mask | business_rules_mask | 
            custom_rules_mask
        )

        stats = {
            "Порожні (NULL)": int(null_mask.values.sum()),
            "Email": int(email_mask.values.sum()),
            "Телефон": int(phone_mask.values.sum()),
            "Дата/Час": int(date_mask.values.sum()),
            "Числа < 0": int(negative_mask.values.sum()),
            "Аномалії віку": int(business_rules_mask.values.sum()),
            "Порушення лімітів": int(custom_rules_mask.values.sum()),
            "Дублікати рядків": int(duplicate_rows_mask.sum())
        }
        
        return final_mask, stats