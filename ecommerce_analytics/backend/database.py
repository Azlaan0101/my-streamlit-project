"""
Backend: database connection layer.
Keeps all raw SQL / connection handling out of the Streamlit UI code.
"""
import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).parent.parent / "data" / "ecommerce.db"


@st.cache_resource
def get_connection():
    """Cached SQLite connection, reused across reruns/pages within a session."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn


def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Run a SQL query against the e-commerce DB and return a DataFrame."""
    conn = get_connection()
    return pd.read_sql_query(sql, conn, params=params)


def database_exists() -> bool:
    return DB_PATH.exists()
