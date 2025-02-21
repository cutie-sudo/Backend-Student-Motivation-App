from flask import Flask, request, jsonify, make_response
from datetime import timedelta
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_mail import Mail
from flask_cors import CORS
from config import Config
import os

# Import models & blueprints
from models import db, TokenBlocklist, Admin, Student, Post, Category, Comment, Subscription, Content
from views.auth import auth_bp
from views.comment import comment_bp
from views.admin import admin_bp
# from views.student import student_bp
# from views.post import post_bp
from views.category import category_bp
# from views.subscription import subscription_bp
# from views.content import content_bp

# Initialize Flask-Mail
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config')

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///motivation.db")  # Use SQLite as default
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # JWT configuration
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "yes12")  # Ensure this is a strong secret in production
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

    # Mail configuration (Fixed issue)
    app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 587))  # Use 465 for SSL
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = os.getenv("faith.nguli@student.moringaschool.com")  # Corrected
    app.config['MAIL_PASSWORD'] = os.getenv("wyrnlfdluxjxarlm")  # Corrected
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv("faith.nguli@student.moringaschool.com")

    # Initialize extensions (Fixed duplicate `db.init_app(app)`)
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)
    mail.init_app(app)

    # Remove the duplicate `db.init_app(app)` call
    with app.app_context():
        db.create_all()  # Ensure tables exist

    # Token blocklist check
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_jwt_header, jwt_payload: dict) -> bool:
        jti = jwt_payload.get("jti")
        return db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar() is not None

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(comment_bp)
    app.register_blueprint(admin_bp)
    # app.register_blueprint(student_bp)
    # app.register_blueprint(post_bp)
    app.register_blueprint(category_bp)
    # app.register_blueprint(subscription_bp)
    # app.register_blueprint(content_bp)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
