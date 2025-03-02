import os
import logging
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import create_access_token
from models import db, Admin, Student

# Get the absolute path to the Firebase service account JSON file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, "../firebase-service-account.json")

# Ensure the service account JSON file exists
if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
    raise FileNotFoundError(f"Firebase service account JSON file not found at {FIREBASE_CREDENTIALS_PATH}")

# Initialize Firebase Admin SDK
cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)

auth_bp = Blueprint("auth_bp", __name__)

# ✅ Google Sign-In Route with CORS
@auth_bp.route("/google_login", methods=["POST"])
def google_login():
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
            user = Admin(username=name, email=email, password="google-auth") if role == "admin" else Student(username=name, email=email, password="google-auth")
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
