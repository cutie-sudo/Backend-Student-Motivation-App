from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, UniqueConstraint
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

metadata = MetaData()
db = SQLAlchemy(metadata=metadata)

# Base User Mixin for common functionality
class UserMixin:
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# Models
class Admin(db.Model, UserMixin):
    __tablename__ = "admins"
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship("Post", backref="created_by_admin", lazy=True)
    categories = db.relationship("Category", backref="created_by_admin", lazy=True)

class Student(db.Model, UserMixin):
    __tablename__ = "students"
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship("Post", backref="created_by_student", lazy=True)
    comments = db.relationship("Comment", backref="commented_by_student", lazy=True)
    subscriptions = db.relationship("Subscription", backref="subscribed_student", lazy=True)
    wishlist = db.relationship("Wishlist", backref="wishlist_student", lazy=True)

class Post(db.Model):
    __tablename__ = "posts"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)
    is_flagged = db.Column(db.Boolean, default=False)
    likes = db.Column(db.Integer, default=0)
    dislikes = db.Column(db.Integer, default=0)
    
    comments = db.relationship("Comment", backref="post_comments", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "is_approved": self.is_approved,
            "is_flagged": self.is_flagged,
            "likes": self.likes,
            "dislikes": self.dislikes
        }

class Comment(db.Model):
    __tablename__ = "comments"
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("comments.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    replies = db.relationship(
        "Comment", backref=db.backref("parent", remote_side=[id]), lazy=True, cascade="all, delete-orphan"
    )

class Category(db.Model):
    __tablename__ = "categories"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=False)
    
    posts = db.relationship("Post", backref="post_category", lazy=True)

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False)  # e.g., 'pending', 'approved', 'rejected'
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    admin = db.relationship('Admin', backref=db.backref('contents', lazy=True))

class Subscription(db.Model):
    __tablename__ = "subscriptions"
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    
    # Prevent duplicate subscriptions
    __table_args__ = (UniqueConstraint("student_id", "category_id", name="uq_student_category"),)

class Wishlist(db.Model):
    __tablename__ = "wishlist"
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    
    # Prevent duplicate wishlist entries
    __table_args__ = (UniqueConstraint("student_id", "post_id", name="uq_student_post"),)

class TokenBlocklist(db.Model):
    __tablename__ = "token_blocklist"
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)