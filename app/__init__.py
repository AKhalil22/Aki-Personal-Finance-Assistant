# Initialize the Flask app and SQLAlchemy, register routes

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Import and register the routes (Initialization)
    with app.app_context():
        from app.routes import main
        app.register_blueprint(main)

        db.create_all() # Create database

    return app
