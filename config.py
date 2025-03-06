import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()  # Ensure environment variables are loaded

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'yes12')
    SQLALCHEMY_DATABASE_URI = 'postgresql://motivationdb_user:D1dnwxcDXjv0lk53Q2yTPQwElMoCCpCh@dpg-cv4vedl2ng1s73fksr0g-a.oregon-postgres.render.com/motivationdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'yes12')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # Flask-Mail Config
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'faith.nguli@student.moringaschool.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'cdcg_bbtf_vlxm_hiea')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'faith.nguli@student.moringaschool.com')
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
