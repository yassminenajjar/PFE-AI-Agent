# app.py
from flask import Flask, request, jsonify
from controller import natural_language_to_sql

app = Flask(__name__)

@app.route('/query', methods=['POST'])
def handle_query():
    data = request.get_json()
    user_input = data.get('question')

    if not user_input:
        return jsonify({"error": "Missing 'question' in request"}), 400

    result = natural_language_to_sql(user_input)

    if result["error"]:
        return jsonify({
            "query": result["query"],
            "error": result["error"]
        }), 500

    return jsonify({
        "query": result["query"],
        "results": result["results"],
        "explanation": result["explanation"]
    })

if __name__ == '__main__':
    app.run(debug=True)
