import os
import cloudinary
import cloudinary.uploader
import re
import smtplib
import traceback
from flask import Blueprint, request, jsonify, url_for, render_template
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, get_jwt, jwt_required
from flask_mail import Message, Mail
from models import db, TokenBlocklist, Admin, Student
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from datetime import datetime, timezone
from flask import current_app
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email_validator import validate_email, EmailNotValidError  

auth_bp = Blueprint("auth_bp", __name__)
mail = Mail()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def is_valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email) is not None

def send_reset_email(recipient_email):
    sender_email = "faith.nguli@student.moringaschool.com"
    app_password = os.getenv("wyrnlfdluxjxarlm")  # Store password securely
    
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = "Password Reset Request"
    
    reset_token = create_access_token(identity=recipient_email, expires_delta=timedelta(minutes=15))
    reset_link = f"http://localhost:5000/reset_password/{reset_token}"
    body = f"Click here to reset your password: {reset_link}"
    message.attach(MIMEText(body, "plain"))
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipient_email, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False



@auth_bp.route("/admin/register", methods=['POST'])
def register_admin():
    data = request.get_json()

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"success": False, "error": "All fields are required"}), 400

    try:
        validated = validate_email(email)  # Now validate_email is defined
        email = validated.email  # Access the validated email
    except EmailNotValidError as e:  # Now EmailNotValidError is defined
        return jsonify({"success": False, "error": f"Invalid email format: {str(e)}"}), 400  # Improved error message

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

        # Create token after commit
        access_token = create_access_token(identity=new_admin.id)

        # Send welcome email
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
                    "role": "admin"  # Role is now hardcoded
                },
                "access_token": access_token
            }
        }), 201
    except Exception as e:  # Catch potential database errors
        db.session.rollback()  # Rollback on error
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
        validated = validate_email(email)  # Now validate_email is defined
        email = validated.email  # Access the validated email
    except EmailNotValidError as e:  # Now EmailNotValidError is defined
        return jsonify({"success": False, "error": f"Invalid email format: {str(e)}"}), 400  # Improved error message

    existing_student = Student.query.filter_by(email=email).first()
    if existing_student:
        return jsonify({"success": False, "error": "Email already exists"}), 400

    hashed_password = generate_password_hash(password)
    new_student = Student(username=username, email=email, password=hashed_password)

    try:
        db.session.add(new_student)
        db.session.commit()

        # Create token after commit
        access_token = create_access_token(identity=new_student.id)

        # Send welcome email
        msg = Message(
            subject="Welcome to Our Platform!",
            recipients=[email],
            body=f"Hi {username},\n\nWelcome to our platform! We're excited to have you on board.\n\nBest regards,\nThe Team"
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
                    "role": "student"  # Role is now hardcoded
                },
                "access_token": access_token
            }
        }), 201
    except Exception as e:  # Catch potential database errors
        db.session.rollback()  # Rollback on error
        return jsonify({"success": False, "error": f"Registration failed: {str(e)}"}), 500

@auth_bp.route("/admin/login", methods=['POST'])  # Separate route for admin login
def admin_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    admin = Admin.query.filter_by(email=email).first()
    if not admin or not check_password_hash(admin.password, password):
        return jsonify({"error": "Invalid email or password"}), 401
    if admin:
        access_token = create_access_token(identity=admin.id)  # Correct: admin.id
        return jsonify({
        "message": "Admin login successful",  # Clearer message
        "access_token": access_token,
        "role": "admin"
    }), 200


@auth_bp.route("/student/login", methods=['POST'])  # Separate route for student login
def student_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    student = Student.query.filter_by(email=email).first()
    if not student or not check_password_hash(student.password, password):
        return jsonify({"error": "Invalid email or password"}), 401
    if student:
        access_token = create_access_token(identity=student.id)  # Correct: student.id
        return jsonify({
        "message": "Student login successful",  # Clearer message
        "access_token": access_token,
        "role": "student"
    }), 200

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"success": False, "error": "Email is required"}), 400

    # Check if user exists in Admin or Student table
    user = Admin.query.filter_by(email=email).first() or Student.query.filter_by(email=email).first()
    
    if user:
        email_sent = send_reset_email(email)  # This function should return True/False
        
        if email_sent:
            return jsonify({"message": "If an account exists, a reset email has been sent"}), 200
        else:
            return jsonify({"message": "Error sending reset email."}), 500  

    return jsonify({"message": "If an account exists, a reset email has been sent"}), 200


def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset')

@auth_bp.route('/request-reset', methods=['POST'])
def request_reset():
    email = request.json.get('email')
    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = Admin.query.filter_by(email=email).first() or Student.query.filter_by(email=email).first()
    if not user:
        # For security, don't reveal if user exists
        return jsonify({"message": "If an account exists with this email, a reset link will be sent"}), 200

    token = generate_reset_token(email)
    reset_url = f"{request.host_url}reset-password/{token}"  # Or your frontend URL

    try:
        # Send email with reset_url
        send_reset_email(email, reset_url)
        return jsonify({"message": "Reset link sent successfully"}), 200
    except Exception as e:
        print(f"Error sending reset email: {e}")
        return jsonify({"error": "Error sending reset email"}), 500

@auth_bp.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    try:
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        email = serializer.loads(token, salt="password-reset", max_age=3600)

        if email is None:  # Check if email is None
            return jsonify({"error": "Invalid or expired token"}), 400

            print(f"Email after check: {email}")  

    except SignatureExpired:
        return jsonify({"error": "Token has expired", "message": "Please request a new password reset link"}), 400

    except BadSignature:
        return jsonify({"error": "Invalid token", "message": "Reset token is invalid or has been tampered with"}), 400

    except Exception as e:
        return jsonify({"error": "Token error", "message": str(e)}), 400

    # Find user (Admin or Student)
    user = Admin.query.filter_by(email=email).first() or Student.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    new_password = request.json.get("new_password")
    if not new_password:
        return jsonify({"error": "New password is required"}), 400

    if len(new_password) < 8:
        return jsonify({"error": "Invalid password", "message": "Password must be at least 8 characters long"}), 400

    user.password = generate_password_hash(new_password)

    try:
        db.session.commit()
        return jsonify({"message": "Password updated successfully!"})
    except Exception as e:
        print(traceback.format_exc())  # Print full traceback
        return jsonify({"error": "Token error", "message": str(e)}), 400


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
            "role": role  # Use the determined role
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

    # Check if username or email already exists
    if username != user.username and (Admin.query.filter_by(username=username).first() or Student.query.filter_by(username=username).first()):
        return jsonify({"status": "error", "message": "Username already exists"}), 400

    if email != user.email and (Admin.query.filter_by(email=email).first() or Student.query.filter_by(email=email).first()):
        return jsonify({"status": "error", "message": "Email already exists"}), 400

    # Update user fields
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