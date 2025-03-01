import os
import re
import jwt
import logging
from flask import Blueprint, request, jsonify, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, get_jwt, jwt_required
from flask_mail import Message, Mail
from models import db, TokenBlocklist, Admin, Student
from datetime import datetime, timezone, timedelta
from email_validator import validate_email, EmailNotValidError
from itsdangerous import URLSafeTimedSerializer
from flask_cors import cross_origin
from authlib.integrations.flask_client import OAuth

auth_bp = Blueprint("auth_bp", __name__)
mail = Mail()

SECRET_KEY = "your_secret_key"
serializer = URLSafeTimedSerializer(SECRET_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OAuth for Google Login
oauth = OAuth()
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://www.googleapis.com/oauth2/v1/userinfo', 
    client_kwargs={'scope': 'openid email profile'},
)

# Google OAuth login route
@auth_bp.route('/google_login')
def google_login():
    redirect_uri = url_for('auth_bp.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

# Google OAuth callback route
@auth_bp.route('/google_login/callback')
def google_callback():
    try:
        token = google.authorize_access_token()
        user_info = google.get('userinfo').json()

        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0])  

        if not email:
            return jsonify({"success": False, "error": "No email provided by Google"}), 400

        user = None
        access_token = None

        if email.endswith('@student.moringaschool.com'):
            user = Student.query.filter_by(email=email).first()
            if not user:
                user = Student(username=name, email=email, password=generate_password_hash('google-oauth-no-password'))
                db.session.add(user)
                db.session.commit()
            access_token = create_access_token(identity={"id": user.id, "role": "student"})

        elif email.endswith('@moringaschool.com') or email.endswith('@admin.moringaschool.com'):
            user = Admin.query.filter_by(email=email).first()
            if not user:
                user = Admin(username=name, email=email, password=generate_password_hash('google-oauth-no-password'))
                db.session.add(user)
                db.session.commit()
            access_token = create_access_token(identity={"id": user.id, "role": "admin"})
        else:
            return jsonify({"success": False, "error": "Unauthorized email domain. Please use a Moringa School email address."}), 403

        return jsonify({
            "success": True,
            "message": "Google login successful!",
            "data": {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": "admin" if isinstance(user, Admin) else "student"
                },
                "access_token": access_token
            }
        }), 200

    except Exception as e:
        logger.error(f"Google login failed: {str(e)}")
        return jsonify({"success": False, "error": f"Google login failed: {str(e)}"}), 500


@auth_bp.route("/admin/login", methods=['POST'])
@cross_origin(origin="http://localhost:5173", supports_credentials=True)
def admin_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    logger.info(f"Admin Login Attempt: {email}")

    admin = Admin.query.filter_by(email=email).first()
    if not admin or not check_password_hash(admin.password, password):
        logger.warning(f"Admin Login Failed: Invalid credentials for {email}")
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = create_access_token(identity={"id": admin.id, "role": "admin"})
    return jsonify({
        "message": "Admin login successful",
        "access_token": access_token,
        "role": "admin"
    }), 200


@auth_bp.route("/student/login", methods=['POST'])
@cross_origin(origin="http://localhost:5173", supports_credentials=True)
def student_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    logger.info(f"Student Login Attempt: {email}")

    student = Student.query.filter_by(email=email).first()
    if not student or not check_password_hash(student.password, password):
        logger.warning(f"Student Login Failed: Invalid credentials for {email}")
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = create_access_token(identity={"id": student.id, "role": "student"})
    return jsonify({
        "message": "Student login successful",
        "access_token": access_token,
        "role": "student"
    }), 200

# Current User Endpoint
@auth_bp.route("/user", methods=["GET"])
@cross_origin(origin="http://localhost:5173", supports_credentials=True)
@jwt_required()
def current_user():
    current_user_info = get_jwt_identity()
    user_id = current_user_info["id"]
    role = current_user_info["role"]

    user = Admin.query.get(user_id) if role == "admin" else Student.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "status": "success",
        "message": "User retrieved",
        "data": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": role
        }
    }), 200


@auth_bp.route("/logout", methods=["DELETE"])
@cross_origin(origin="http://localhost:5173", supports_credentials=True)
@jwt_required()
def logout():
    jti = get_jwt().get("jti")
    if not jti:
        return jsonify({"status": "error", "message": "Token invalid"}), 400

    now = datetime.now(timezone.utc)
    db.session.add(TokenBlocklist(jti=jti, created_at=now))
    db.session.commit()

    return jsonify({"status": "success", "message": "Logged out successfully"}), 200
