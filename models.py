from sqlalchemy import UniqueConstraint, Boolean  # Add this import
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

# Initialize SQLAlchemy

db = SQLAlchemy()



# UserMixin provides authentication methods, no need to redefine
class Admin(db.Model, UserMixin):
    __tablename__ = "admins"
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    github_id = db.Column(db.String(100))
    profile_pic = db.Column(db.String(255), nullable=True, default="default.png")
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    posts = db.relationship("Post", backref="created_by_admin", lazy=True)
    categories = db.relationship("Category", backref="created_by_admin", lazy=True)

class Student(db.Model, UserMixin):
    __tablename__ = "students"
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    github_id = db.Column(db.String(100))
    profile_pic = db.Column(db.String(255), nullable=True, default="default.png")
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    posts = db.relationship("Post", backref="created_by_student", lazy=True)
    comments = db.relationship("Comment", backref="commented_by_student", lazy=True)
    subscriptions = db.relationship("Subscription", back_populates="student")
    wishlist = db.relationship("Wishlist", back_populates="student", overlaps="wishlists_entries")
    
    # Fixed relationships with Share model
    shared_posts = db.relationship("Share", foreign_keys="Share.student_id", back_populates="student", overlaps="received_shares,another_shares") 
    received_shares = db.relationship("Share", foreign_keys="Share.shared_with", back_populates="shared_with_student", overlaps="shared_posts,another_shares") 
    another_shares = db.relationship("Share", foreign_keys="Share.another_fk", back_populates="another_relation", overlaps="shared_posts,received_shares")

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
    shares = db.relationship("Share", back_populates="post")
    wishlist_entries = db.relationship("Wishlist", back_populates="post")


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
    __tablename__ = "content"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    
    admin = db.relationship('Admin', backref=db.backref('contents', lazy=True))
    category = db.relationship('Category', backref=db.backref('contents', lazy=True))


class Notification(db.Model):
    __tablename__ = "notifications"
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=True)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship("Student", backref=db.backref("notifications", lazy=True))


class Share(db.Model):
    __tablename__ = "shares"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    shared_with = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    another_fk = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship(
        "Student",
        foreign_keys=[student_id],
        back_populates="shared_posts",
        overlaps="shared_with_student,another_relation"
    )
    
    # Fixed relationship name to match the column
    shared_with_student = db.relationship(
        "Student",
        foreign_keys=[shared_with],  # Use the column name, not shared_with_id
        back_populates="received_shares",
        overlaps="student,another_relation"
    )
    
    another_relation = db.relationship(
        "Student",
        foreign_keys=[another_fk],
        back_populates="another_shares",
        overlaps="student,shared_with_student"
    )

    # Relationship to Post
    post = db.relationship("Post", back_populates="shares")
    

class UserPreference(db.Model):
    __tablename__ = "user_preferences"
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    preference_type = db.Column(db.String(50), nullable=False)  # e.g., 'technology', 'difficulty_level'
    preference_value = db.Column(db.String(50), nullable=False)  # e.g., 'python', 'beginner'
    
    __table_args__ = (UniqueConstraint("student_id", "preference_type", "preference_value", name="uq_student_preference"),)
    
    student = db.relationship("Student", backref=db.backref("preferences", lazy=True))

class Subscription(db.Model):
    __tablename__ = "subscriptions"
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    
    # Prevent duplicate subscriptions
    __table_args__ = (UniqueConstraint("student_id", "category_id", name="uq_student_category"),)

    student = db.relationship("Student", back_populates="subscriptions")
    category = db.relationship("Category", backref="subscriptions")

class Wishlist(db.Model):
    __tablename__ = "wishlist"
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    
    # Prevent duplicate wishlist entries
    __table_args__ = (UniqueConstraint("student_id", "post_id", name="uq_student_post"),)

    student = db.relationship("Student", backref="wishlists_entries", overlaps="wishlist,wishlist_student")
    post = db.relationship("Post", backref="wishlists_entries")

class TokenBlocklist(db.Model):
    __tablename__ = "token_blocklist"
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Reset Token Methods (Moved Outside Class)
def get_reset_token(user, secret_key, expires_sec=1800):
    s = Serializer(secret_key, expires_sec)
    return s.dumps({'user_id': user.id, 'user_type': user.__class__.__name__.lower()})

def verify_reset_token(token, secret_key):
    s = Serializer(secret_key)
    try:
        data = s.loads(token)
        user_type = data.get('user_type')
        user_id = data.get('user_id')
        Model = Admin if user_type == 'admin' else Student
        return Model.query.get(user_id)
    except:
        return None