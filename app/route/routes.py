from flask import Flask
from app.controller.query_controller import query_controller

def register_routes(app: Flask):
    app.register_blueprint(query_controller)