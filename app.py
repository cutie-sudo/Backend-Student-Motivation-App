import os
from datetime import timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_cors import CORS
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from views.profile import profile_bp

# Import db and TokenBlocklist from models
from models import db, TokenBlocklist

# Import blueprints
from views.auth import auth_bp
from views.comment import comment_bp
from views.admin import admin_bp
from views.student import student_bp
from views.post import post_bp
from views.category import category_bp
from views.content import content_bp
from views.subscription import subscription_bp
from views.wishlist import wishlist_bp
from views.share import share_bp
from views.preference import preference_bp
from views.notification import notification_bp

# Initialize extensions
mail = Mail()
jwt = JWTManager()
login_manager = LoginManager()

load_dotenv()

def create_app():
    app = Flask(__name__)

    # Load configuration from config.py
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your_default_secret_key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "your_jwt_secret")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

    # Mail configuration from environment variables
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")





    # CORS configuration: allow frontend URL with credentials
    CORS(app, supports_credentials=True, origins=[app.config.get("FRONTEND_URL", "motiviationapp-d4cm.vercel.app")])

    # Initialize database and migrations
    db.init_app(app)
    migrate = Migrate(app, db)

    mail.init_app(app)
    jwt.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "auth_bp.google_login"

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(comment_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(post_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(content_bp)
    app.register_blueprint(subscription_bp)
    app.register_blueprint(wishlist_bp)
    app.register_blueprint(share_bp)
    app.register_blueprint(preference_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(profile_bp, url_prefix="")  # profile_bp registers routes like /profile and /profile/picture

    # Token blocklist check
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_jwt_header, jwt_payload: dict) -> bool:
        jti = jwt_payload.get("jti")
        return db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar() is not None

    # Error handling
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({"error": "Internal server error"}), 500

    return app


    app = create_app()
  
