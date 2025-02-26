import pytest
from app import app, db
from models import Post, Admin, Student
from flask_jwt_extended import create_access_token

@pytest.fixture
def client():
    app.config["TESTING"] = True
    # app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:motivation:"
    # app.config["JWT_SECRET_KEY"] = "test_secret"

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

@pytest.fixture
def admin_token():
    """Create an admin user and return a JWT token."""
    with app.app_context():
        admin = Admin(id=1, email="admin@example.com", password="hashed_password")
        db.session.add(admin)
        db.session.commit()
        return create_access_token(identity=admin.id)

@pytest.fixture
def student_token():
    """Create a student user and return a JWT token."""
    with app.app_context():
        student = Student(id=2, email="student@example.com", password="hashed_password")
        db.session.add(student)
        db.session.commit()
        return create_access_token(identity=student.id)

@pytest.fixture
def sample_post():
    """Create a sample post."""
    with app.app_context():
        post = Post(id=1, title="Sample Post", content="This is a test post", category_id=1, student_id=2)
        db.session.add(post)
        db.session.commit()
        return post


def test_add_post(client, student_token):
    """Test adding a new post."""
    headers = {"Authorization": f"Bearer {student_token}"}
    data = {"title": "Test Post", "content": "This is a test", "category_id": 1}

    response = client.post("/posts", json=data, headers=headers)
    assert response.status_code == 201
    assert response.json["message"] == "Post added successfully"

def test_get_posts(client, sample_post):
    """Test retrieving all posts."""
    response = client.get("/posts")
    assert response.status_code == 200
    assert len(response.json) > 0

def test_get_post(client, sample_post):
    """Test retrieving a specific post."""
    response = client.get(f"/{sample_post.id}")
    assert response.status_code == 200
    assert response.json["title"] == "Sample Post"

def test_update_post(client, student_token, sample_post):
    """Test updating a post."""
    headers = {"Authorization": f"Bearer {student_token}"}
    data = {"title": "Updated Post", "content": "Updated content"}

    response = client.put(f"/{sample_post.id}", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json["message"] == "Post updated successfully"

def test_unauthorized_update_post(client, admin_token, sample_post):
    """Test that a non-owner cannot update the post."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    data = {"title": "Hacked Post"}

    response = client.put(f"/{sample_post.id}", json=data, headers=headers)
    assert response.status_code == 403
    assert response.json["message"] == "Unauthorized: You can only update posts you created"

def test_delete_post(client, student_token, sample_post):
    """Test deleting a post."""
    headers = {"Authorization": f"Bearer {student_token}"}

    response = client.delete(f"/{sample_post.id}", headers=headers)
    assert response.status_code == 200
    assert response.json["message"] == "Post deleted successfully"

def test_unauthorized_delete_post(client, admin_token, sample_post):
    """Test that a non-owner cannot delete the post."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.delete(f"/{sample_post.id}", headers=headers)
    assert response.status_code == 403
    assert response.json["message"] == "Unauthorized: You can only delete posts you created"

def test_like_post(client, student_token, sample_post):
    """Test liking a post."""
    headers = {"Authorization": f"Bearer {student_token}"}

    response = client.post(f"/{sample_post.id}/like", headers=headers)
    assert response.status_code == 200
    assert response.json["message"] == "Post liked successfully"

def test_dislike_post(client, student_token, sample_post):
    """Test disliking a post."""
    headers = {"Authorization": f"Bearer {student_token}"}

    response = client.post(f"/{sample_post.id}/dislike", headers=headers)
    assert response.status_code == 200
    assert response.json["message"] == "Post disliked successfully"
