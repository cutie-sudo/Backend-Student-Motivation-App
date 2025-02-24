import os
import cloudinary
import cloudinary.uploader
import re
import jwt
import smtplib
import logging
import traceback
from flask import Blueprint, request, jsonify, url_for, render_template
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, get_jwt, jwt_required
from flask_mail import Message, Mail
from models import db, TokenBlocklist, Admin, Student
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timezone
from flask import current_app, flash, redirect, url_for
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email_validator import validate_email, EmailNotValidError
from itsdangerous import URLSafeTimedSerializer

 


auth_bp = Blueprint("auth_bp", __name__)


mail = Mail()

SECRET_KEY = "your_secret_key"
serializer = URLSafeTimedSerializer(SECRET_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def is_valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email) is not None


@auth_bp.route("/login/github")
def github_login():
    return github.authorize(callback=url_for('auth_bp.github_authorized', _external=True))

@auth_bp.route("/login/github/authorized")
def github_authorized():
    resp = github.authorized_response()
    if resp is None or resp.get('access_token') is None:
        return 'Access denied: reason={} error={}'.format(
            request.args['error_reason'],
            request.args['error_description']
        )

    github_token = resp['access_token']
    github = oauth.remote_app('github', access_token=github_token)
    resp = github.get('/user')
    if not resp.ok:
        return "Failed to fetch user info from GitHub."

    user_info = resp.json()
    github_id = str(user_info["id"])  # GitHub ID is an integer, convert to string
    email = user_info.get("email", "")
    username = user_info.get("login", "")

    # Check if the user already exists in the database
    user = Admin.query.filter_by(email=email).first() or Student.query.filter_by(email=email).first()

    if not user:
        # Create a new user (you can decide whether to create an Admin or Student)
        # For example, create a Student by default
        user = Student(
            username=username,
            email=email,
            password=generate_password_hash(github_id)  # Use GitHub ID as a placeholder password
        )
        db.session.add(user)
        db.session.commit()

    # Log the user in
    login_user(user)
    return f"Logged in as {user.username} <a href='/logout'>Logout</a>"



@auth_bp.route("/admin/register", methods=['POST'])
def register_admin():
    data = request.get_json()

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"success": False, "error": "All fields are required"}), 400

    try:
        validated = validate_email(email)  
        email = validated.email  
    except EmailNotValidError as e: 
        return jsonify({"success": False, "error": f"Invalid email format: {str(e)}"}), 400 

    existing_admin = Admin.query.filter_by(email=email).first()
    if existing_admin:
        return jsonify({"success": False, "error": "Email already exists"}), 400

    existing_username = Admin.query.filter_by(username=username).first()
    if existing_username:
        return jsonify({"success": False, "error": "Username already exists"}), 400

    hashed_password = generate_password_hash(password)
    new_admin = Admin(username=username, email=email, password=hashed_password)

    try:
        db.session.add(new_admin)
        db.session.commit()

        
        access_token = create_access_token(identity=new_admin.id)

        
        msg = Message(
            subject="Welcome to Our Platform!",
            sender="faith.nguli@student.moringaschool.com",
            recipients=[email],
            body=f"Hi {username},\n\nWelcome to TechElevate platform! We're excited to have you on board. \n\nBest regards,\nThe TechElevate Team"
        )
        mail.send(msg)

        return jsonify({
            "success": True,
            "message": "Admin registration successful!",
            "data": {
                "user": {
                    "id": new_admin.id,
                    "username": new_admin.username,
                    "email": new_admin.email,
                    "role": "admin"  
                },
                "access_token": access_token
            }
        }), 201
    except Exception as e:  
        db.session.rollback()  
        return jsonify({"success": False, "error": f"Registration failed: {str(e)}"}), 500




@auth_bp.route("/student/register", methods=['POST'])
def register_student():
    data = request.get_json()

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"success": False, "error": "All fields are required"}), 400

    try:
        validated = validate_email(email)  
        email = validated.email  
    except EmailNotValidError as e:  
        return jsonify({"success": False, "error": f"Invalid email format: {str(e)}"}), 400  

    existing_student = Student.query.filter_by(email=email).first()
    if existing_student:
        return jsonify({"success": False, "error": "Email already exists"}), 400

    hashed_password = generate_password_hash(password)
    new_student = Student(username=username, email=email, password=hashed_password)

    try:
        db.session.add(new_student)
        db.session.commit()

        
        access_token = create_access_token(identity=new_student.id)

       
        msg = Message(
            subject="Welcome to Our Platform!",
            sender="faith.nguli@student.moringaschool.com",
            recipients=[email],
            body=f"Hi {username},\n\nWelcome to our TechElevate! We are committed to helping you stay motivated, grow, and achieve your academic and personal goals\n\nBest regards,\nThe TechElevate Team"
        )
        mail.send(msg)

        return jsonify({
            "success": True,
            "message": "Student registration successful!",
            "data": {
                "user": {
                    "id": new_student.id,
                    "username": new_student.username,
                    "email": new_student.email,
                    "role": "student"  
                },
                "access_token": access_token
            }
        }), 201
    except Exception as e:  
        db.session.rollback() 
        return jsonify({"success": False, "error": f"Registration failed: {str(e)}"}), 500

@auth_bp.route("/admin/login", methods=['POST'])  
def admin_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    admin = Admin.query.filter_by(email=email).first()
    if not admin or not check_password_hash(admin.password, password):
        return jsonify({"error": "Invalid email or password"}), 401
    if admin:
        access_token = create_access_token(identity=admin.id)  
        return jsonify({
        "message": "Admin login successful",  
        "access_token": access_token,
        "role": "admin"
    }), 200


@auth_bp.route("/student/login", methods=['POST'])  
def student_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    student = Student.query.filter_by(email=email).first()
    if not student or not check_password_hash(student.password, password):
        return jsonify({"error": "Invalid email or password"}), 401
    if student:
        access_token = create_access_token(identity=student.id)  
        return jsonify({
        "message": "Student login successful", 
        "access_token": access_token,
        "role": "student"
    }), 200

def generate_reset_token(email):
    admin = Admin.query.filter_by(email=email).first()
    if admin:
        role = "admin"
        user_id = admin.id
    else:
        student = Student.query.filter_by(email=email).first()
        if student:
            role = "student"
            user_id = student.id
        else:
            return None  

    payload = {
        "sub": user_id,
        "role": role,  
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm="HS256")

def send_password_reset_email(user, reset_url):
    try:
        subject = "Password Reset Request"
        msg = Message(
            subject,
            recipients=[user.email]
        )
        
        msg.body = f"""
        To reset your password, visit the following link:
        {reset_url}
        
        If you did not make this request, simply ignore this email.
        
        This link will expire in 30 minutes.
        """
        
        msg.html = f"""
        <h2>Password Reset Request</h2>
        <p>To reset your password, click the following link:</p>
        <p><a href="{reset_url}">Reset Password</a></p>
        <p>If you did not make this request, simply ignore this email.</p>
        <p>This link will expire in 30 minutes.</p>
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send reset email: {str(e)}")
        return False

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    try:
        admin = Admin.query.filter_by(email=email).first()
        student = Student.query.filter_by(email=email).first()
        user = admin if admin else student
        
        if user:
            token = user.get_reset_token()
            reset_url = url_for('auth_bp.reset_password', token=token, _external=True)
            
            if send_password_reset_email(user, reset_url):
                return jsonify({"message": "Password reset instructions have been sent to your email."}), 200
            else:
                return jsonify({"error": "Error sending reset email. Please try again."}), 500
        else:
            return jsonify({"message": "If an account exists with this email, you will receive reset instructions."}), 200
            
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

def set_password(new_password):
    """Dummy password update function - replace with actual logic"""
    print(f"Password updated to: {new_password}")

@auth_bp.route('/test-email')
def test_email():
    try:
        msg = Message(
            'Test Email',
            recipients=['your-test-email@example.com']
        )
        msg.body = 'This is a test email.'
        mail.send(msg)
        return 'Email sent successfully!'
    except Exception as e:
        return f'Error sending email: {str(e)}'


@auth_bp.route('/request-password-reset', methods=['POST'])
def request_password_reset():
    from app import mail  

    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({"message": "Email is required"}), 400

    
    user = Admin.query.filter_by(email=email).first() or \
           Student.query.filter_by(email=email).first()

    if not user:
        return jsonify({"message": "Admin or Student with this email does not exist"}), 404

  
    token = serializer.dumps(email, salt="password-reset-salt")

    
    msg = Message(
        subject="Password Reset Request",
        recipients=[email],
        body=f"Click the link to reset your password: http://localhost:5000/reset-password/{token}"
    )

    try:
        mail.send(msg)  
        logger.info(f"Password reset email sent to {email}")
        return jsonify({"message": "Password reset email sent successfully"}), 200
    except Exception as e:
        logger.error(f"Error sending email to {email}: {str(e)}")
        return jsonify({"message": "Error sending email", "error": str(e)}), 500



@auth_bp.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    data = request.json
    new_password = data.get('new_password')

    if not new_password:
        return jsonify({"message": "New password is required"}), 400

    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=3600)  
    except SignatureExpired:
        return jsonify({"message": "Token expired"}), 400
    except Exception:
        return jsonify({"message": "Invalid token"}), 400

    
    user = Admin.query.filter_by(email=email).first() or \
           Student.query.filter_by(email=email).first()

    if not user:
        return jsonify({"message": "Admin or Student with this email does not exist"}), 404

    
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    return jsonify({"message": "Password reset successfully"}), 200


def update_password(user, new_password, user_type):
    """
    Generic password update function for both admin and student
    """
    try:
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        user.password = hashed_password
        db.session.commit()
        logger.debug(f"Password updated successfully for {user_type}: {user.username if hasattr(user, 'username') else user.registration_number}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating {user_type} password: {e}")
        return False




@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    user = Admin.query.get(current_user_id) or Student.query.get(current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"message": "Access granted", "user": {"id": user.id, "email": user.email, "role": "admin" if isinstance(user, Admin) else "student"}})

@auth_bp.route("/user", methods=["GET"])
@jwt_required()
def current_user():
    current_user_id = get_jwt_identity()

    admin = Admin.query.get(current_user_id)
    student = Student.query.get(current_user_id)

    if admin:
        user = admin
        role = "admin"
    elif student:
        user = student
        role = "student"
    else:
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

@auth_bp.route("/user/update", methods=["PUT"])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    user = Admin.query.get(current_user_id) or Student.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid input"}), 400

    username = data.get("username", user.username)
    email = data.get("email", user.email)

    
    if username != user.username and (Admin.query.filter_by(username=username).first() or Student.query.filter_by(username=username).first()):
        return jsonify({"status": "error", "message": "Username already exists"}), 400

    if email != user.email and (Admin.query.filter_by(email=email).first() or Student.query.filter_by(email=email).first()):
        return jsonify({"status": "error", "message": "Email already exists"}), 400

    
    user.username = username
    user.email = email
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Profile updated successfully",
        "data": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": "admin" if isinstance(user, Admin) else "student"
        }
    }), 200

@auth_bp.route("/user/profile", methods=["GET"])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = Admin.query.get(current_user_id) or Student.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "username": user.username,
        "email": user.email,
        "role": "admin" if isinstance(user, Admin) else "student"
    }), 200

@auth_bp.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
    jti = get_jwt().get("jti")
    if not jti:
        return jsonify({"status": "error", "message": "Token invalid"}), 400

    now = datetime.now(timezone.utc)
    db.session.add(TokenBlocklist(jti=jti, created_at=now))
    db.session.commit()

    return jsonify({"status": "success", "message": "Logged out successfully"}), 200



