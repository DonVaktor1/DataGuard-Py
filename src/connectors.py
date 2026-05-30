import pandas as pd
from pymongo import MongoClient
from sqlalchemy import create_engine, inspect, text
import streamlit as st

@st.cache_resource
def get_sql_engine(conn_string):
    return create_engine(conn_string, pool_pre_ping=True, pool_size=5, max_overflow=10)

@st.cache_resource
def get_mongo_client(conn_string):
    return MongoClient(conn_string)

def clear_connector_cache():
    get_sql_engine.clear()
    get_mongo_client.clear()

class DBConnector:
    def __init__(self, conn_string):
        self.conn_string = conn_string

    def _get_engine(self):
        return get_sql_engine(self.conn_string)

    def _get_mongo_db(self):
        client = get_mongo_client(self.conn_string)
        db_name = self.conn_string.split('/')[-1].split('?')[0]
        return client[db_name]

    def fetch_data(self, target, limit=100):
        try:
            if self.conn_string.startswith(("postgresql", "mysql", "sqlite", "mssql")):
                engine = self._get_engine()
                with engine.connect() as conn:
                    return pd.read_sql(text(target), conn)

            elif self.conn_string.startswith("mongodb"):
                db = self._get_mongo_db()
                cursor = db[target].find().limit(limit)
                df = pd.DataFrame(list(cursor))
                if not df.empty and '_id' in df.columns:
                    del df['_id']
                return df

            else:
                raise ValueError("Цей тип бази даних поки не підтримується")
        except Exception as e:
            raise e

    def get_table_names(self):
        try:
            if "mongodb" in self.conn_string.lower():
                db = self._get_mongo_db()
                return db.list_collection_names()
            else:
                engine = self._get_engine()
                inspector = inspect(engine)
                return inspector.get_table_names()
        except Exception as e:
            st.warning(f"Не вдалося отримати таблиці: {e}")
            return []