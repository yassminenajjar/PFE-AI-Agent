# controller.py
import google.generativeai as genai
import pandas as pd
import pyodbc
from db_config import setup_database_connection

# === Load Gemini model ===
genai.configure(api_key="AIzaSyA_F6QrdhtzQ-VPWQVugsGNWX9sg9EjN7Y")  # 🔁 Replace this with your real API key
model = genai.GenerativeModel('gemini-1.5-pro-latest')

# === Setup DB Connection ===
conn, cursor = setup_database_connection()

# === Get schema info ===
def get_schema(cursor):
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

SCHEMA_INFO = get_schema(cursor)

# === Few-shot prompt ===
def get_few_shot_examples():
    return """=== FEW-SHOT EXAMPLES ===
    
    [SIMPLE QUERY - COUNT]
    User: "Count breaks for Plant A in January 2024"
    SQL: SELECT SUM(num_of_break) FROM wirebreakDetails WHERE Plant = 'A' AND MONTH(Break_date) = 1 AND YEAR(Break_date) = 2024
    Response: "Plant A had 127 wire breaks in January 2024."

    [SIMPLE QUERY - LIST]
    User: "Show machines with >15 breaks last month"
    SQL: SELECT Machine_Number, SUM(num_of_break) FROM wirebreakDetails WHERE Break_date >= DATEADD(month, -1, GETDATE()) GROUP BY Machine_Number HAVING SUM(num_of_break) > 15
    Response: "Machines exceeding 15 breaks: M-107 (23), M-203 (18)."

    [REPORT - TREND ANALYSIS]
    User: "Analyze break trends by week for Plant B"
    SQL: SELECT Week_Number, SUM(num_of_break) FROM wirebreakDetails WHERE Plant = 'B' GROUP BY Week_Number ORDER BY Week_Number
    Response: '''
    **Summary**: Breaks peaked in Week 32 (42 incidents), 58% higher than average.
    **Root Cause**: 80% of Week 32 breaks were on Machine M-107 with diameter < 0.3mm.
    **Next Steps**: Inspect M-107's tension settings and review Supplier Gamma's 0.3mm wires.
    '''

    [REPORT - COMPARISON]
    User: "Compare material vs process breaks by supplier"
    SQL: SELECT w.Supplier, b.typeB, COUNT(*) FROM wirebreakDetails w JOIN wirebreaktype b ON w.Wire_Break_Type = b.wirebreaktype GROUP BY w.Supplier, b.typeB
    Response: '''
    **Summary**: Supplier Alpha has 3x more material breaks (45) than process breaks (15).
    **Root Cause**: Alpha's material breaks correlate with humidity > 80%.
    **Next Steps**: Store Alpha's wires in climate-controlled areas during summer.
    '''

    [COMPLEX JOIN]
    User: "Find batches with breaks outside diameter specs"
    SQL: SELECT w.Batch_Number FROM wirebreakDetails w JOIN machinetype m ON w.Machine_Number = m.machinetype WHERE w.Break_Diameter < m.minBreakDiameter OR w.Break_Diameter > m.maxBreakDiameter
    Response: "Batches with out-of-spec diameters: BX-205, BX-209 (all from Supplier Alpha)."

    [TIME-BASED ANALYSIS]
    User: "Show monthly consumption vs break rates"
    SQL: SELECT MONTH(Break_date) AS month, SUM(c.Real_Consumption), SUM(w.num_of_break)/SUM(c.Real_Consumption) FROM wirebreakDetails w JOIN wireConsumption c ON w.Plant = c.Plant AND w.Week_Number = c.Week_Number GROUP BY MONTH(Break_date)
    Response: '''
    **Trend**: Break rate doubled in July (0.15 breaks/ton) vs June (0.07).
    **Threshold**: Rates exceed 0.1 when temperature > 30°C.
    **Action**: Implement cooling systems for wires in summer months.
    '''
    """  

# === Convert NL → SQL → Answer ===
def natural_language_to_sql(user_query):
    prompt = f"""
    {get_few_shot_examples()}

    Database Schema:
    {SCHEMA_INFO}

    Convert this to SQL (ONLY the query):
    "{user_query}"
    """
    response = model.generate_content(prompt)
    sql_query = response.text.strip().replace('```sql', '').replace('```', '').strip()

    try:
        cursor.execute(sql_query)
        columns = [column[0] for column in cursor.description]
        results = cursor.fetchall()
        df = pd.DataFrame.from_records(results, columns=columns)
    except Exception as e:
        return {
            "query": sql_query,
            "results": None,
            "error": str(e),
            "explanation": None
        }

    is_report = any(word in user_query.lower() for word in ["analyze", "report", "trend", "compare", "summary", "breakdown"])
    explanation_prompt = f"""
    {get_few_shot_examples()}

    Database Schema: {SCHEMA_INFO}
    User Question: {user_query}
    SQL Used: {sql_query}
    Results: {str(df)}

    {"Generate a MANAGER-READY report with **Summary/Root Cause/Next Steps** sections." if is_report else "Answer concisely like the simple examples above."}
    """
    explanation = model.generate_content(explanation_prompt)

    return {
        "query": sql_query,
        "results": df.to_dict(orient='records'),
        "error": None,
        "explanation": explanation.text
    }
