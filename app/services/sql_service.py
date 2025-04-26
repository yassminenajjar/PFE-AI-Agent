import pandas as pd

def execute_query(sql_query, cursor):
    """Execute a SQL query and return results as a DataFrame"""
    try:
        cursor.execute(sql_query)
        columns = [column[0] for column in cursor.description]
        results = cursor.fetchall()
        return pd.DataFrame.from_records(results, columns=columns)
    except Exception as e:
        return f"Error executing query: {str(e)}"