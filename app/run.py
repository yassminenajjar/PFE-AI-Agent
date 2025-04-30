from flask import Flask
from flask_cors import CORS
from app.route.routes import register_routes

def create_app():
    app = Flask(__name__)
    register_routes(app)
    return app

app = create_app()
CORS(app)

if __name__ == "__main__":
    app.run(debug=True)