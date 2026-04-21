import pandas as pd
from sqlalchemy import create_engine, text

class DBConnector:
    def __init__(self, conn_string):
        self.conn_string = conn_string

    def fetch_data(self, target):
        if self.conn_string.startswith(("postgresql", "mysql", "sqlite")):
            engine = create_engine(self.conn_string)
            with engine.connect() as conn:
                return pd.read_sql(text(target), conn)
        
        elif self.conn_string.startswith("mongodb"):
            from pymongo import MongoClient
            client = MongoClient(self.conn_string)
            db_name = self.conn_string.split('/')[-1].split('?')[0]
            db = client[db_name]
            cursor = db[target].find()
            df = pd.DataFrame(list(cursor))
            if '_id' in df.columns: del df['_id'] # Прибираємо системні ID Mongo
            return df
            
        else:
            raise ValueError("Цей тип бази даних поки не підтримується")