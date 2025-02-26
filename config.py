import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()  # Ensure environment variables are loaded

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'yes12')  # Use os.getenv safely
    SQLALCHEMY_DATABASE_URI = 'sqlite:///motivation.db' # Fix the app.config issue
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'yes12')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # Flask-Mail Config
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('faith.nguli@student.moringaschool.com')
    MAIL_PASSWORD = os.getenv('cdcg bbtf vlxm hiea')
    MAIL_DEFAULT_SENDER = 'faith.nguli@student.moringaschool.com'
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
