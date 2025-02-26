import pytest
from app import db, app
from models import Admin, Student
from flask_jwt_extended import decode_token

@pytest.fixture
def client():
    app.config["TESTING"] = True  # Ensure test mode is enabled

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_register_admin(client):
    """Test admin registration"""
    response = client.post("/admin/register", json={
        "username": "admin_test",
        "email": "admin@test.com",
        "password": "securepassword"
    })
    data = response.get_json()
    assert response.status_code == 201
    assert data["success"] is True
    assert data["data"]["user"]["email"] == "admin@test.com"

def test_register_existing_admin(client):
    """Test registering an admin with an existing email"""
    client.post("/admin/register", json={
        "username": "admin1",
        "email": "admin@test.com",
        "password": "securepassword"
    })
    response = client.post("/admin/register", json={
        "username": "admin2",
        "email": "admin@test.com",
        "password": "securepassword"
    })
    data = response.get_json()
    assert response.status_code == 400
    assert "Email already exists" in data["error"]

def test_login_admin(client):
    """Test admin login"""
    client.post("/admin/register", json={
        "username": "admin_test",
        "email": "admin@test.com",
        "password": "securepassword"
    })
    response = client.post("/admin/login", json={
        "email": "admin@test.com",
        "password": "securepassword"
    })
    data = response.get_json()
    assert response.status_code == 200
    assert "access_token" in data

def test_invalid_login(client):
    """Test login with incorrect credentials"""
    response = client.post("/admin/login", json={
        "email": "admin@test.com",
        "password": "wrongpassword"
    })
    data = response.get_json()
    assert response.status_code == 401
    assert "Invalid email or password" in data["error"]

def test_register_student(client):
    """Test student registration"""
    response = client.post("/student/register", json={
        "username": "student_test",
        "email": "student@test.com",
        "password": "securepassword"
    })
    data = response.get_json()
    assert response.status_code == 201
    assert data["success"] is True
    assert data["data"]["user"]["email"] == "student@test.com"

def test_login_student(client):
    """Test student login"""
    client.post("/student/register", json={
        "username": "student_test",
        "email": "student@test.com",
        "password": "securepassword"
    })
    response = client.post("/student/login", json={
        "email": "student@test.com",
        "password": "securepassword"
    })
    data = response.get_json()
    assert response.status_code == 200
    assert "access_token" in data

# def test_forgot_password(client):
#     """Test forgot password endpoint"""
#     client.post("/admin/register", json={
#         "username": "admin_test",
#         "email": "admin@test.com",
#         "password": "securepassword"
#     })
#     response = client.post("/forgot-password", json={"email": "admin@test.com"})
#     data = response.get_json()
#     assert response.status_code == 200
#     assert "Password reset instructions have been sent" in data["message"]
