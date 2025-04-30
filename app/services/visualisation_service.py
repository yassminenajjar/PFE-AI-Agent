import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
import json

def smart_visualization_fallback(df, user_query):
    try:
        num_cols = len(df.columns)
        if num_cols == 1:
            fig = px.histogram(df, x=df.columns[0], title=f"Distribution of {df.columns[0]}")
        elif num_cols == 2:
            x_col, y_col = df.columns[0], df.columns[1]
            if df[x_col].nunique() < 10 and df[y_col].nunique() > 10:
                fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
            elif pd.api.types.is_datetime64_any_dtype(df[x_col]):
                fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} over time")
            else:
                fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
        else:
            fig = px.scatter_matrix(df, title="Multi-variable Relationships")
        return fig
    except Exception as e:
        print(f"Automatic visualization failed: {str(e)}")
        return None

def determine_chart_type(df, numeric_cols, date_cols, cat_cols):
    num_cols = len(df.columns)
    if len(date_cols) >= 1 and len(numeric_cols) >= 1:
        return "line chart" if len(df) > 10 else "bar chart"
    elif len(cat_cols) >= 1 and len(numeric_cols) >= 1:
        if len(df) <= 7:
            return "pie chart"
        elif df[numeric_cols[0]].nunique() <= 12:
            return "bar chart"
        else:
            return "histogram"
    elif len(numeric_cols) >= 2:
        return "scatter plot"
    else:
        return "bar chart"

def generate_plotly_code(df, user_query, model):
    num_cols = len(df.columns)
    num_rows = len(df)
    date_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
    numeric_cols = [col for col in df.columns if np.issubdtype(df[col].dtype, np.number)]
    cat_cols = [col for col in df.columns if col not in numeric_cols + date_cols]
    chart_type = determine_chart_type(df, numeric_cols, date_cols, cat_cols)
    prompt = f"""
    DATAFRAME STRUCTURE:
    - Shape: {num_rows} rows × {num_cols} columns
    - Numeric columns: {numeric_cols}
    - Categorical columns: {cat_cols}
    - Date columns: {date_cols}
    - Suggested chart type: {chart_type}

    USER QUESTION: \"{user_query}\"

    Generate Plotly visualization code with these requirements:
    1. MUST start with `import plotly.graph_objects as go`
    2. Use {chart_type} as the primary chart type
    3. Include proper titles and axis labels based on the user query
    4. Make the visualization clear and professional
    5. Return ONLY the Python code wrapped in ```python ``` blocks

    Example for bar chart:
    ```python
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['category'], y=df['value']))
    fig.update_layout(title='Clear Title', xaxis_title='X Label', yaxis_title='Y Label')
    ```
    """
    response = model.generate_content(prompt)
    code = response.text.strip()
    if '```python' in code:
        code = code.split('```python')[1].split('```')[0].strip()
    return code

def execute_plotly_code(code, df, user_query):
    if not code or not isinstance(df, pd.DataFrame) or df.empty:
        return smart_visualization_fallback(df, user_query)
    try:
        allowed_objects = {
            'go': go,
            'px': px,
            'df': df.copy(),
            'make_subplots': make_subplots,
            'np': np,
            'pd': pd
        }
        exec(code, allowed_objects)
        fig = None
        for fig_name in ['fig', 'figure', 'plot']:
            if fig_name in allowed_objects:
                fig = allowed_objects[fig_name]
                break
        if fig is None:
            return smart_visualization_fallback(df, user_query)
        if not fig.layout.title.text:
            fig.update_layout(title=user_query[:50])
        if not fig.layout.xaxis.title.text and len(df.columns) > 0:
            fig.update_layout(xaxis_title=df.columns[0])
        if not fig.layout.yaxis.title.text and len(df.columns) > 1:
            fig.update_layout(yaxis_title=df.columns[1])
        return fig
    except Exception as e:
        print(f"Visualization code execution failed: {str(e)}")
        return smart_visualization_fallback(df, user_query)

def generate_plotly_js_code(df, user_query, model):
    prompt = f"""
    Given the following SQL query results as a JSON array:

    {json.dumps(df.to_dict(orient='records'))}

    Generate JavaScript code using Plotly.js to visualize this data. 
    - Use Plotly.newPlot(container, data, layout).
    - Use the container variable directly (not a string id).
    - The code must be ready to run in a browser.
    - The code must define data and layout, and then call Plotly.newPlot.
    - Do not include any HTML or Python code, only JavaScript.
    - Return only the JavaScript code, no explanations or markdown.

    Example:
    var data = [...];
    var layout = {...};
    Plotly.newPlot(container, data, layout);
    """

    response = model.generate_content(prompt)
    code = response.text.strip()
    # Optionally, strip markdown/code block formatting if present
    if '```' in code:
        code = code.split('```')[1].strip()
    return code