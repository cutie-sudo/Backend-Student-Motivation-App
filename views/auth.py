import os
import logging
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import create_access_token
from models import db, Admin, Student
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash  
from sqlalchemy.exc import IntegrityError

# Get the absolute path to the Firebase service account JSON file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Fixed typo: _file -> _file_
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, "../firebase-service-account.json")

# Initialize Firebase Admin SDK only if not already initialized
if not firebase_admin._apps:
    if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
        raise FileNotFoundError(
            f"Firebase service account JSON file not found at {FIREBASE_CREDENTIALS_PATH}"
        )
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

auth_bp = Blueprint("auth_bp", __name__)  # Fixed typo: _name -> _name_

# ---------------------------------------------------
# No more add_cors_headers function — we rely on @cross_origin
# ---------------------------------------------------

# Google Sign-In Route with proper CORS handling
@auth_bp.route("/google_login", methods=["POST", "OPTIONS"])
@cross_origin(origins="*", supports_credentials=True)
def google_login():
    # Handle Preflight (OPTIONS request) if needed
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200

    try:
        data = request.get_json()
        id_token = data.get("idToken")
        if not id_token:
            return jsonify({"success": False, "error": "No ID token provided"}), 400

        decoded_token = firebase_auth.verify_id_token(id_token)
        email = decoded_token.get("email")
        name = decoded_token.get("name") or email.split('@')[0]

        role = "student"
        user = Student.query.filter_by(email=email).first()

        if email.endswith('@admin.moringaschool.com'):
            role = "admin"
            user = Admin.query.filter_by(email=email).first()

        if not user:
            if role == "admin":
                user = Admin(username=name, email=email, password="google-auth")
            else:
                user = Student(username=name, email=email, password="google-auth")
            db.session.add(user)
            db.session.commit()

        access_token = create_access_token(identity={"id": user.id, "role": role})

        return jsonify({
            "success": True,
            "message": "Google login successful!",
            "data": {"id": user.id, "username": user.username, "email": user.email, "role": role},
            "access_token": access_token
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# Local Signup Route with CORS handling
@auth_bp.route("/signup", methods=["POST", "OPTIONS"])
@cross_origin(origins="*", supports_credentials=True)
def signup():
    if request.method == "OPTIONS":
        response = jsonify({"message": "CORS preflight successful"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response
    

    try:
        data = request.get_json()
        firstName = data.get("firstName")
        lastName = data.get("lastName")
        email = data.get("email")
        password = data.get("password")
        role = data.get("role", "student").lower()

        if not all([firstName, lastName, email, password]):
            return jsonify({"success": False, "error": "Missing required fields."}), 400

        if role == "admin":
            user = Admin(
                email=email,
                username=f"{firstName} {lastName}",
                password=generate_password_hash(password)
            )
        else:
            user = Student(
                email=email,
                username=f"{firstName} {lastName}",
                password=generate_password_hash(password)
            )

        db.session.add(user)
        db.session.commit()

        # Create an access token for the newly registered user
        access_token = create_access_token(identity={"id": user.id, "role": role})

        return jsonify({
            "success": True,
            "message": "User registered successfully!",
            "data": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": role
            },
            "access_token": access_token  # Return the access token
        }), 200

    except IntegrityError:
        db.session.rollback()
        return jsonify({"success": False, "error": "User already exists."}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# Profile Route with CORS handling
@auth_bp.route("/profile", methods=["GET", "OPTIONS"])
@cross_origin(origins="*", supports_credentials=True)
def profile():
    # Handle Preflight (OPTIONS request) if needed
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200

    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "error": "Missing or invalid token"}), 401

        token = auth_header.split(" ")[1]
        decoded_token = firebase_auth.verify_id_token(token)

        email = decoded_token.get("email")
        role = "student"
        user = Student.query.filter_by(email=email).first()

        if email.endswith('@admin.moringaschool.com'):
            role = "admin"
            user = Admin.query.filter_by(email=email).first()

        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        return jsonify({
            "success": True,
            "data": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": role
            }
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@auth_bp.route('/login', methods=['POST'])
@cross_origin(origins="*", supports_credentials=True)
def login():
    try:
        data = request.json
        print("Received login request:", data)  # Debug print

        email = data.get("email")
        password = data.get("password")
        role = data.get("role")

        if not email or not password or not role:
            print("Missing credentials")  # Debug print
            return jsonify({"error": "Email, password, and role are required"}), 400

        role = role.lower()
        if role not in ["admin", "student"]:
            print("Invalid role:", role)  # Debug print
            return jsonify({"error": "Invalid role. Must be 'admin' or 'student'"}), 403

        # Check Student or Admin separately
        if role == "student":
            student = Student.query.filter_by(email=email).first()
            if not student:
                print("Student not found")  # Debug print
                return jsonify({"error": "Invalid login credentials"}), 401

            # ✅ Password check for student
            if not check_password_hash(student.password, password):
                print("Incorrect password for student")  # Debug print
                return jsonify({"error": "Invalid login credentials"}), 401

            # Generate JWT token
            access_token = create_access_token(identity={"id": student.id, "email": student.email, "role": "student"})
            print("Login successful for student:", email)  # Debug print

            return jsonify({"access_token": access_token, "student": {"email": student.email, "role": "student"}}), 200

        elif role == "admin":
            admin = Admin.query.filter_by(email=email).first()
            if not admin:
                print("Admin not found")  # Debug print
                return jsonify({"error": "Invalid login credentials"}), 401

            # ✅ Password check for admin
            if not check_password_hash(admin.password, password):
                print("Incorrect password for admin")  # Debug print
                return jsonify({"error": "Invalid login credentials"}), 401

            # Generate JWT token
            access_token = create_access_token(identity={"id": admin.id, "email": admin.email, "role": "admin"})
            print("Login successful for admin:", email)  # Debug print

            return jsonify({"access_token": access_token, "admin": {"email": admin.email, "role": "admin"}}), 200

    except Exception as e:
        print("Login error:", str(e))  # Debugging
        return jsonify({"error": str(e)}), 500  # Show real error
