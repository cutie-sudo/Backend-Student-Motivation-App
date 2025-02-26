import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from models import db, Admin, Student, Post
from app import post_bp  # Ensure correct import


@pytest.fixture
def app():
    """Create a Flask test app and initialize the database."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test_secret_key"

    db.init_app(app)
    jwt = JWTManager(app)  

    app.register_blueprint(post_bp, url_prefix="/")  

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def admin_token(app):
    """Create an admin and return a JWT token."""
    with app.app_context():
        admin = Admin(id=1, email="admin@example.com", username="admin123", password="hashed_password")
        db.session.add(admin)
        db.session.commit()
        return create_access_token(identity=admin.id)


@pytest.fixture
def student_token(app):
    """Create a student and return a JWT token."""
    with app.app_context():
        student = Student(id=2, email="student@example.com", username="student123", password="hashed_password")
        db.session.add(student)
        db.session.commit()
        return create_access_token(identity=student.id)


@pytest.fixture
def sample_post(app):
    """Create and return a post in the database."""
    with app.app_context():
        post = Post(title="Sample Post", content="Sample Content", category_id=1, student_id=2)
        db.session.add(post)
        db.session.commit()
        return post.id  # ✅ Return post ID instead of object


def test_get_posts(client, sample_post):
    """Test retrieving all posts."""
    response = client.get("/posts")  # ✅ Ensure correct route
    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert len(response.json) > 0


def test_get_post(client, sample_post, app):
    """Test retrieving a specific post."""
    with app.app_context():
        post = Post.query.get(sample_post)  # ✅ Query the post again

    response = client.get(f"/{post.id}")

    assert response.status_code == 200
    post_data = response.json
    assert post_data["title"] == post.title
    assert post_data["content"] == post.content


def test_add_post(client, student_token):
    """Test adding a new post."""
    headers = {"Authorization": f"Bearer {student_token}"}
    data = {"title": "New Post", "content": "New Content", "category_id": 1}

    response = client.post("/posts", json=data, headers=headers)

    assert response.status_code == 201
    assert response.json["message"] == "Post added successfully"


def test_update_post(client, student_token, sample_post, app):
    """Test updating a post."""
    with app.app_context():
        post = Post.query.get(sample_post)  # ✅ Query the post again

    headers = {"Authorization": f"Bearer {student_token}"}
    data = {"title": "Updated Title", "content": "Updated Content"}

    response = client.put(f"/{post.id}", json=data, headers=headers)

    assert response.status_code == 200
    assert response.json["message"] == "Post updated successfully"


def test_unauthorized_update_post(client, admin_token, sample_post, app):
    """Test unauthorized post update (only creator can update)."""
    with app.app_context():
        post = Post.query.get(sample_post)  # ✅ Query the post again

    headers = {"Authorization": f"Bearer {admin_token}"}
    data = {"title": "Unauthorized Update"}

    response = client.put(f"/{post.id}", json=data, headers=headers)

    assert response.status_code == 403
    assert response.json["message"] == "Unauthorized: You can only update posts you created"


def test_delete_post(client, student_token, sample_post, app):
    """Test deleting a post."""
    with app.app_context():
        post = Post.query.get(sample_post)  # ✅ Query the post again

    headers = {"Authorization": f"Bearer {student_token}"}

    response = client.delete(f"/{post.id}", headers=headers)

    assert response.status_code == 200
    assert response.json["message"] == "Post deleted successfully"


def test_unauthorized_delete_post(client, admin_token, sample_post, app):
    """Test unauthorized post deletion (only creator can delete)."""
    with app.app_context():
        post = Post.query.get(sample_post)  # ✅ Query the post again

    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.delete(f"/{post.id}", headers=headers)

    assert response.status_code == 403
    assert response.json["message"] == "Unauthorized: You can only delete posts you created"


def test_like_post(client, student_token, sample_post, app):
    """Test liking a post."""
    with app.app_context():
        post = Post.query.get(sample_post)  # ✅ Query the post again

    headers = {"Authorization": f"Bearer {student_token}"}

    response = client.post(f"/{post.id}/like", headers=headers)

    assert response.status_code == 200
    assert "likes" in response.json


def test_dislike_post(client, student_token, sample_post, app):
    """Test disliking a post."""
    with app.app_context():
        post = Post.query.get(sample_post)  # ✅ Query the post again

    headers = {"Authorization": f"Bearer {student_token}"}

    response = client.post(f"/{post.id}/dislike", headers=headers)

    assert response.status_code == 200
    assert "dislikes" in response.json
