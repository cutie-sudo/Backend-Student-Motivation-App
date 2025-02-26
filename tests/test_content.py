import pytest
from flask_jwt_extended import create_access_token
from app import app, db  # Import your existing Flask app instance
from models import Content, Category, Admin

@pytest.fixture
def client():
    """Set up test client and database."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:motivation:"  # Use in-memory database for testing
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

@pytest.fixture
def auth_headers(client):
    """Create a test admin and return authentication headers."""
    with app.app_context():
        admin = Admin(username="testadmin", email="admin@test.com", password="password")
        db.session.add(admin)
        db.session.commit()

        access_token = create_access_token(identity=admin.id)
        return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def test_admin():
    """Create a test admin only if it does not exist."""
    with app.app_context():
        admin = Admin.query.filter_by(username="testadmin").first()
        if not admin:
            admin = Admin(username="testadmin", email="admin@test.com", password="password")
            db.session.add(admin)
            db.session.commit()

        # Refresh to keep it bound to session
        db.session.refresh(admin)
        return admin


@pytest.fixture
def test_category(test_admin):
    """Create a test category linked to an admin."""
    with app.app_context():
        category = Category.query.filter_by(name="Test Category").first()
        if not category:
            category = Category(name="Test Category", admin_id=test_admin.id)
            db.session.add(category)
            db.session.commit()

        db.session.refresh(category)  # Keep it bound to session
        return category


@pytest.fixture
def test_content(test_category):
    """Create a test content item."""
    with app.app_context():
        content = Content(
            title="Sample Content",
            description="This is a sample description",
            category_id=test_category.id,
            status="pending",
            user_id=1  # Assuming admin ID is 1
        )
        db.session.add(content)
        db.session.commit()
        return content

def test_add_content(client, auth_headers, test_category):
    """Test adding new content."""
    data = {
        "title": "New Content",
        "description": "This is new content",
        "category_id": test_category.id
    }
    response = client.post("/content", json=data, headers=auth_headers)
    assert response.status_code == 201
    assert "Content added successfully" in response.json["message"]

def test_get_all_content(client, test_content):
    """Test retrieving all content."""
    response = client.get("/content")
    assert response.status_code == 200
    assert len(response.json) > 0
    assert response.json[0]["title"] == "Sample Content"

def test_get_content(client, test_content, auth_headers):
    """Test retrieving specific content by ID."""
    response = client.get(f"/content/{test_content.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json["title"] == "Sample Content"

def test_update_content(client, test_content, auth_headers):
    """Test updating content."""
    data = {
        "title": "Updated Content",
        "description": "Updated description",
        "status": "approved"
    }
    response = client.put(f"/content/{test_content.id}", json=data, headers=auth_headers)
    assert response.status_code == 200
    assert "Content updated successfully" in response.json["message"]

def test_unauthorized_update_content(client, test_content):
    """Test unauthorized user trying to update content."""
    data = {"title": "Unauthorized Update"}
    response = client.put(f"/content/{test_content.id}", json=data)
    assert response.status_code == 401  # Unauthorized (No JWT Token)

def test_delete_content(client, test_content, auth_headers):
    """Test deleting content."""
    response = client.delete(f"/content/{test_content.id}", headers=auth_headers)
    assert response.status_code == 200
    assert "Content deleted successfully" in response.json["message"]

def test_unauthorized_delete_content(client, test_content):
    """Test unauthorized user trying to delete content."""
    response = client.delete(f"/content/{test_content.id}")
    assert response.status_code == 401  # Unauthorized (No JWT Token)
