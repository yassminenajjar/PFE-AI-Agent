from flask import Blueprint, request, jsonify
from app.services.database_services import setup_database_connection, get_schema
from app.services.llm_services import configure_llm
from app.services.nl_to_sql_service import natural_language_to_sql

query_controller = Blueprint('query_controller', __name__)

# Set up DB and LLM model once at startup (for demo; for production, consider connection pooling)
conn, cursor = setup_database_connection()
schema_info = get_schema(cursor)
model = configure_llm()

@query_controller.route('/api/nl-to-sql', methods=['POST'])
def nl_to_sql_endpoint():
    data = request.json
    user_query = data.get('question')
    if not user_query:
        return jsonify({"error": "Missing 'question' in request body"}), 400

    result = natural_language_to_sql(user_query, model, cursor, schema_info)

    # Convert DataFrame to JSON if results are a DataFrame
    if hasattr(result['results'], 'to_dict'):
        result['results'] = result['results'].to_dict(orient='records')

    return jsonify(result)