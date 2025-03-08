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
from flask import send_from_directory
import logging

from models import db, TokenBlocklist
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
from views.profile import profile_bp

# Initialize extensions
mail = Mail()
jwt = JWTManager()
login_manager = LoginManager()

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    # Load configuration from environment variables
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your_default_secret_key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "your_jwt_secret")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

    # Mail configuration
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

    # CORS configuration - use one consistent approach
    # We'll use the flask-cors extension with all necessary settings
    CORS(
        app,
        resources={r"/*": {
            "origins": ["https://students-motiviation-app.vercel.app"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }}
    )

    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)
    mail.init_app(app)
    jwt.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "auth_bp.google_login"

    # Register blueprints
    app.register_blueprint(auth_bp)
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
    app.register_blueprint(profile_bp, url_prefix="/profile")  # Explicitly set the prefix

    # Token blocklist check
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_jwt_header, jwt_payload: dict) -> bool:
        jti = jwt_payload.get("jti")
        return db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar() is not None

    # Root route handler to prevent 404 errors
    @app.route('/')
    def index():
        return jsonify({"message": "Student Motivation API is running"}), 200

    # Error handling
    @app.errorhandler(404)
    def not_found(error):
        app.logger.info(f"404 error: {request.path}")
        return jsonify({"error": "Not found"}), 404

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.error(f"500 error: {str(error)}")
        return jsonify({"error": "Internal server error"}), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unhandled exception: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

    @app.route('/images/<path:filename>')
    def serve_static_images(filename):
        return send_from_directory('static/images', filename)

    # Log all requests for debugging (optional, remove in production)
    @app.before_request
    def log_request_info():
        app.logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")

    return app

# ✅ Only for local development
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)