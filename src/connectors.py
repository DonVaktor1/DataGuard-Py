import pandas as pd
from pymongo import MongoClient
from sqlalchemy import create_engine, inspect, text
import streamlit as st

class DBConnector:
    def __init__(self, conn_string):
        self.conn_string = conn_string

    def _get_engine(self):
        if "db_engine" not in st.session_state:
            st.session_state.db_engine = create_engine(self.conn_string, pool_pre_ping=True)
        return st.session_state.db_engine

    def fetch_data(self, target):
        try:
            if self.conn_string.startswith(("postgresql", "mysql", "sqlite", "mssql")):
                engine = self._get_engine()
                with engine.connect() as conn:
                    return pd.read_sql(text(target), conn)
            
            elif self.conn_string.startswith("mongodb"):
                client = MongoClient(self.conn_string)
                db_name = self.conn_string.split('/')[-1].split('?')[0]
                db = client[db_name]
                cursor = db[target].find()
                df = pd.DataFrame(list(cursor))
                if not df.empty and '_id' in df.columns: 
                    del df['_id']
                return df
            else:
                raise ValueError("Цей тип бази даних поки не підтримується")
        except Exception as e:
            if "db_engine" in st.session_state: 
                del st.session_state.db_engine
            raise e
        
    def get_table_names(self):
        try:
            if "mongodb" in self.conn_string.lower():
                client = MongoClient(self.conn_string)
                db_name = self.conn_string.split('/')[-1].split('?')[0]
                return client[db_name].list_collection_names()
            else:
                engine = self._get_engine()
                inspector = inspect(engine)
                return inspector.get_table_names()
        except:
            return []