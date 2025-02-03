# Configuration settings for Flask, SQLAlchemy, etc.

from datetime import timedelta

class Config:
    SECRET_KEY = "CS50P"
    SQLALCHEMY_DATABASE_URI = "sqlite:///users.sqlite3"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=5)  # Correct timedelta format
