import pandas as pd
from constants import EMAIL_REGEX, PHONE_REGEX

class DataValidator:

    @staticmethod
    def get_error_masks(df, custom_rules=[], column_types={}):
        null_mask = df.isna()

        if df.empty:
            return null_mask, {k: 0 for k in [
                "Порожні (NULL)", "Email", "Телефон",
                "Дата/Час", "Числа < 0", "Аномалії віку",
                "Порушення лімітів", "Дублікати рядків"
            ]}

        string_df = df.astype(str).apply(lambda x: x.str.strip().str.lower())
        null_mask = null_mask | string_df.isin(["", "none", "nan", "null"])

        numeric_df = df.apply(pd.to_numeric, errors='coerce')
        negative_mask = (numeric_df < 0).fillna(False)

        email_mask          = pd.DataFrame(False, index=df.index, columns=df.columns)
        phone_mask          = pd.DataFrame(False, index=df.index, columns=df.columns)
        date_mask           = pd.DataFrame(False, index=df.index, columns=df.columns)
        business_rules_mask = pd.DataFrame(False, index=df.index, columns=df.columns)
        custom_rules_mask   = pd.DataFrame(False, index=df.index, columns=df.columns)

        df_hashable         = df.apply(lambda col: col.map(lambda x: str(x) if isinstance(x, (dict, list)) else x))
        duplicate_rows_mask = df_hashable.duplicated(keep=False)

        for col in df.columns:
            col_l   = col.lower()
            col_str = string_df[col]

            if any(x in col_l for x in ["email", "mail"]):
                email_mask[col] = ~col_str.str.match(EMAIL_REGEX) & ~null_mask[col]

            if any(x in col_l for x in ["phone", "tel"]):
                phone_mask[col] = ~col_str.str.match(PHONE_REGEX) & ~null_mask[col]

            if any(x in col_l for x in ["date", "time"]):
                date_mask[col] = pd.to_datetime(df[col], errors='coerce').isna() & ~null_mask[col]

            if "age" in col_l or "вік" in col_l:
                business_rules_mask[col] = (
                    (numeric_df[col] < 0) | (numeric_df[col] > 120)
                ) & ~null_mask[col]

        for rule in custom_rules:
            col = rule.get('column')
            if col not in df.columns:
                continue

            op        = rule.get('operator')
            limit     = rule.get('value')
            col_type  = column_types.get(col, "число")  

            if col_type == "число":
                val = numeric_df[col]
                if op == ">":    m = (val <= limit)
                elif op == "<":  m = (val >= limit)
                elif op == ">=": m = (val < limit)
                elif op == "<=": m = (val > limit)
                elif op == "==": m = (val != limit)
                else: continue

            else:
                if op == "містить":
                    m = ~string_df[col].str.contains(str(limit), na=False)
                elif op == "не_містить":
                    m = string_df[col].str.contains(str(limit), na=False)
                elif op == "починається з":
                    m = ~string_df[col].str.startswith(str(limit), na=False)
                elif op == "регулярний вираз":
                    try:
                        m = ~string_df[col].str.contains(str(limit), regex=True, na=False)
                    except Exception:
                        continue
                else:
                    continue

            custom_rules_mask[col] = (
                custom_rules_mask[col] | (m & ~null_mask[col]).fillna(False)
            )

        final_mask = (
            null_mask | negative_mask | date_mask |
            email_mask | phone_mask | business_rules_mask |
            custom_rules_mask | duplicate_rows_mask
        )

        stats = {
            "Порожні (NULL)":    int(null_mask.values.sum()),
            "Email":             int(email_mask.values.sum()),
            "Телефон":           int(phone_mask.values.sum()),
            "Дата/Час":          int(date_mask.values.sum()),
            "Числа < 0":         int(negative_mask.values.sum()),
            "Аномалії віку":     int(business_rules_mask.values.sum()),
            "Порушення лімітів": int(custom_rules_mask.values.sum()),
            "Дублікати рядків":  int(duplicate_rows_mask.sum()),
        }

        return final_mask, stats