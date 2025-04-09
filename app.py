from flask import Flask, request, jsonify
from nl_to_sql import natural_language_to_sql
import pandas as pd  # Add this import

app = Flask(__name__)

@app.route('/query', methods=['POST'])
def handle_query():
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({"error": "Please provide a 'question' in the request body"}), 400
    
    response = natural_language_to_sql(data['question'])
    
    return jsonify({
        "sql_query": response["query"],
        "results": response["results"].to_dict(orient='records') if isinstance(response["results"], pd.DataFrame) else str(response["results"]),
        "explanation": response["explanation"]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)