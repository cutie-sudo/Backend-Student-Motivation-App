import os
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_cors import CORS
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_dance.contrib.github import make_github_blueprint
from config import Config
from models import Admin, Student, Post, Comment, Category, Content, Subscription, Wishlist, TokenBlocklist, db, Share,  UserPreference
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from threading import Thread
from authlib.integrations.flask_client import OAuth
from requests_oauthlib import OAuth2Session  


# Initialize extensions
mail = Mail()
jwt = JWTManager()
login_manager = LoginManager()


app = Flask(__name__)

oauth = OAuth(app)

app.config.from_object('config')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///motivation.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT configuration
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "supersecretkey")  # Use a secure key in production
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

# Mail configuration
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME", "faith.nguli@student.moringaschool.com")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD", "cdcg bbtf vlxm hiea")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER", "faith.nguli@student.moringaschool.com")

CORS(app, origins="http://localhost:5173", supports_credentials=True)

google = oauth.register(
    name='google',
    client_id="722343203611-eb58frc154op8i74a4kufv464q5nhifm.apps.googleusercontent.com",
    client_secret="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",
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    client_kwargs={'scope': 'openid email profile'}
)


# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    # Try loading from both Student and Admin tables
    student = Student.query.get(int(user_id))
    if student:
        return student
    return Admin.query.get(int(user_id))


# Initialize extensions
migrate = Migrate(app, db)
db.init_app(app)
mail.init_app(app)
jwt.init_app(app)
login_manager.init_app(app)


login_manager.login_view = "github.login"
# GitHub OAuth blueprint
github_bp = make_github_blueprint(
    client_id=os.getenv("GITHUB_CLIENT_ID", "Ov23liqNiPP1Y2tGyRog"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET", "4f124d6654d27cff5f98693622bea4e508a91558"),
    redirect_to="github_login"
)

app.register_blueprint(github_bp, url_prefix="/login")

# Register blueprints
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



# Token blocklist check
@jwt.token_in_blocklist_loader
def check_if_token_revoked(_jwt_header, jwt_payload: dict) -> bool:
    jti = jwt_payload.get("jti")
    return db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar() is not None


if __name__ == '__main__':
    app.run(debug=True)

