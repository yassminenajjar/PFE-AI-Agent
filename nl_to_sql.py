import pyodbc
import google.generativeai as genai
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv
import os
import pandas as pd

# Initialize Gemini
genai.configure(api_key="AIzaSyA_F6QrdhtzQ-VPWQVugsGNWX9sg9EjN7Y")
model = genai.GenerativeModel('gemini-1.5-pro-latest')

# Database connection
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=PC-GHILEB;"
    "DATABASE=WireBreak;"
    "Trusted_Connection=yes;"
)
cursor = conn.cursor()

def get_schema():
    cursor.execute("""
        SELECT t.name AS table_name, c.name AS column_name, ty.name AS type_name
        FROM sys.tables t
        JOIN sys.columns c ON t.object_id = c.object_id
        JOIN sys.types ty ON c.user_type_id = ty.user_type_id
        ORDER BY t.name, c.column_id
    """)
    schema = {}
    for table, column, dtype in cursor.fetchall():
        schema.setdefault(table, []).append(f"{column} ({dtype})")
    return "\n".join([f"{table}({', '.join(cols)})" for table, cols in schema.items()])

SCHEMA_INFO = get_schema()

def execute_query(sql_query):
    try:
        cursor.execute(sql_query)
        columns = [column[0] for column in cursor.description]
        results = cursor.fetchall()
        return pd.DataFrame.from_records(results, columns=columns)
    except Exception as e:
        return f"Error executing query: {str(e)}"

def natural_language_to_sql(user_query):
    # Generate SQL from natural language
    prompt = f"""
    You are a SQL Server expert. Use this database schema:
    {SCHEMA_INFO}
    
    Convert this natural language query to SQL:
    \"{user_query}\"
    
    Return ONLY the SQL query, nothing else.
    """
    
    response = model.generate_content(prompt)
    sql_query = response.text.strip().replace('```sql', '').replace('```', '').strip()
    
    # Execute the query
    results = execute_query(sql_query)
    
    # Generate human-like explanation
    explanation_prompt = f"""
    The user asked: \"{user_query}\"
    We executed this SQL query: {sql_query}
    The database returned these results: {str(results)}
    
    Provide a concise, human-like answer to the user's original question using these results.
    Write as if you're answering directly to the user (use \"we\", \"you\", etc.).
    Don't mention the SQL query or technical details.
    If there's an error, explain what might be wrong in simple terms.
    """
    
    explanation = model.generate_content(explanation_prompt)
    
    return {
        "query": sql_query,
        "results": results,
        "explanation": explanation.text
    }