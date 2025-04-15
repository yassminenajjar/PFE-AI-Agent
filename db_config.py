# db_config.py
import pyodbc

def setup_database_connection():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=PC-GHILEB;"
        "DATABASE=WireBreak;"
        "Trusted_Connection=yes;"
    )
    return conn, conn.cursor()
