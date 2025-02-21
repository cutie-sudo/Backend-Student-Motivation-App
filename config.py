import os
from dotenv import load_dotenv

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///motivation.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-Mail Config
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'faith.nguli@student.moringaschool.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'jwrdrsivgslucaxf')
    MAIL_DEFAULT_SENDER = 'faith.nguli@student.moringaschool.com'


    load_dotenv()
