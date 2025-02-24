# tests/test_auth.py
import pytest
from flask_jwt_extended import create_access_token
from app import db

def test_admin_register(client, db_session):  # Inject db_session
    data = {
        "username": "testadmin_reg",  # Unique username for each test
        "email": "admin_reg@test.com",  # Unique email
        "password": "testpassword"
    }
    response = client.post("/admin/register", json=data)
    assert response.status_code == 201
    assert "access_token" in response.json["data"]

def test_student_register(client, db_session):  # Inject db_session
    data = {
        "username": "teststudent_reg",  # Unique username
        "email": "student_reg@test.com",  # Unique email
        "password": "testpassword"
    }
    response = client.post("/student/register", json=data)
    assert response.status_code == 201
    assert "access_token" in response.json["data"]

def test_admin_login(client, admin_user, db_session):  # Inject db_session
    data = {
        "email": "admin@test.com",
        "password": "testpassword"
    }
    response = client.post("/admin/login", json=data)
    assert response.status_code == 200
    assert "access_token" in response.json

def test_student_login(client, student_user, db_session):  # Inject db_session
    data = {
        "email": "student@test.com",
        "password": "testpassword"
    }
    response = client.post("/student/login", json=data)
    assert response.status_code == 200
    assert "access_token" in response.json

def test_protected_admin(client, admin_user, db_session):  # Inject db_session
    access_token = create_access_token(identity=admin_user.id)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 200
    assert response.json["user"]["role"] == "admin"

def test_protected_student(client, student_user, db_session):  # Inject db_session
    access_token = create_access_token(identity=student_user.id)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 200
    assert response.json["user"]["role"] == "student"

def test_current_user_admin(client, admin_user, db_session):  # Inject db_session
    access_token = create_access_token(identity=admin_user.id)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/user", headers=headers)
    assert response.status_code == 200
    assert response.json["data"]["role"] == "admin"

def test_current_user_student(client, student_user, db_session):  # Inject db_session
    access_token = create_access_token(identity=student_user.id)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/user", headers=headers)
    assert response.status_code == 200
    assert response.json["data"]["role"] == "student"

def test_update_profile_admin(client, admin_user, db_session):  # Inject db_session
    access_token = create_access_token(identity=admin_user.id)
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "username": "updatedadmin",
        "email": "updatedadmin@test.com"
    }
    response = client.put("/user/update", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json["data"]["username"] == "updatedadmin"

def test_update_profile_student(client, student_user, db_session):  # Inject db_session
    access_token = create_access_token(identity=student_user.id)
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "username": "updatedstudent",
        "email": "updatedstudent@test.com"
    }
    response = client.put("/user/update", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json["data"]["username"] == "updatedstudent"

def test_logout(client, admin_user, db_session):  # Inject db_session
    access_token = create_access_token(identity=admin_user.id)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.delete("/logout", headers=headers)
    assert response.status_code == 200
    assert response.json["message"] == "Logged out successfully"