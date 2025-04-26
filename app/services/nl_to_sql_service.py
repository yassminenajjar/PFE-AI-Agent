from app.services.visualisation_service import generate_plotly_code, execute_plotly_code
from .sql_service import execute_query
from .llm_services import generate_content
import pandas as pd

def is_relevant_query(user_query, model, schema_info):
    prompt = f"""
    You are a database query classifier. Your task is to determine if this user query:
    \"{user_query}\"

    is relevant to a database with this schema:
    {schema_info}

    Respond with ONLY 'True' if the query is relevant and can be answered with this database,
    or 'False' if the query is completely unrelated to this database context.
    """
    response = model.generate_content(prompt)
    return response.strip().lower() == 'true'

def natural_language_to_sql(user_query, model, cursor, schema_info):
    prompt = f"""
    Database Schema:
    {schema_info}

    Convert this to SQL (ONLY the query, using SQL Server syntax):
    - Use YEAR() instead of strftime('%Y')
    - Use MONTH() instead of strftime('%m')
    - Use DAY() instead of strftime('%d')
    - Use CONVERT() for date formatting
    - If you use ORDER BY, always include the ordered column(s) in both the SELECT and GROUP BY clauses.


    User query: \"{user_query}\"
    """
    sql_query = generate_content(model, prompt).replace('```sql', '').replace('```', '').strip()
    results = execute_query(sql_query, cursor)
    is_report = any(keyword in user_query.lower() for keyword in 
                   ["analyze", "report", "trend", "compare", "summary", "breakdown"])
    report_instruction = """Generate output EXACTLY in this format:

    [Report Title Brief Description]

    - [Item 1]: [Metric] ([Percentage if available])
    - [Item 2]: [Metric]
    - (...)

    Helpful Insights: [The top 3(if possible) remarks made from the result of SQL query execution,The remarks provided need to be helpful to a Business Intelligence perspective].

    Suggested Actions: [The top 3(if possible) actions that needs to be done about the remarks made in the Helpful Insights section even if the insights are not enough for you to suggest actions , suggest the ones you would if you were running a multi million dollar company that produces cables for car manufacturing and other industries  ].

    RULES:
    1. Title must be <10 words
    2. List all the items returned in the results of the SQL execution result 
    3. Helpful Insights must include a percentage or multiplier
    4. Suggested Actions must specify both what and where
    5. Never show SQL or technical details
    6. Use same punctuation/capitalization as example"""

    if is_report:
        explanation_prompt = f"""
        Database Context:
        {schema_info}

        User Question: {user_query}
        SQL Used: {sql_query}
        Query Results: {str(results)}

        {report_instruction}

        STRICT FORMATTING:
        - Blank line after title
        - Dash-start for list items
        - "Helpful Insights:" and "Suggested Actions:" labels exactly as shown
        """
    else:
        explanation_prompt = f"""
        Database Context:
        {schema_info}

        User Question: {user_query}
        SQL Used: {sql_query}
        Query Results: {str(results)}

        Answer in 1 line with the key number.

        STRICT FORMATTING:
        - No report structure, just answer the question directly.
        - Do NOT provide Helpful Insights or Suggested Actions.
        """

    explanation = generate_content(model,explanation_prompt)

    if isinstance(results, str) and results.startswith("Error"):
        plotly_code = None
        visualization = None
    else:
        plotly_code = generate_plotly_code(results, user_query, model)
        visualization = execute_plotly_code(plotly_code, results, user_query)
    return {
        "query": sql_query,
        "results": results,
        "explanation": explanation,
        "visualization": visualization,
        "plotly_code": plotly_code
    }