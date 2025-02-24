import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app import create_app, db  # Assuming create_app is in app.py
from models import Admin, Student  # Assuming models are in models.py

@pytest.fixture(scope='session')
def app():
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test_secret_key",
        "MAIL_SUPPRESS_SEND": True,
        "JWT_SECRET_KEY": "test_jwt_secret"
    }

    app = create_app(test_config)

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db_session(app):
    with app.app_context():
        session = db.session()
        yield session
        session.rollback()
        session.close()

@pytest.fixture
def admin_user(app, db_session):
    admin = Admin.query.filter_by(username="testadmin").first()
    if admin:
        db_session.delete(admin)
        db_session.commit()

    admin = Admin(username="testadmin", email="admin@test.com", password="testpassword")
    db_session.add(admin)
    db_session.commit()
    yield admin

    Admin.query.filter_by(username="testadmin").delete()
    db_session.commit()

@pytest.fixture
def student_user(app, db_session):
    student = Student.query.filter_by(username="teststudent").first()
    if student:
        db_session.delete(student)
        db_session.commit()

    student = Student(username="teststudent", email="student@test.com", password="testpassword")
    db_session.add(student)
    db_session.commit()
    yield student

    Student.query.filter_by(username="teststudent").delete()
    db_session.commit()




