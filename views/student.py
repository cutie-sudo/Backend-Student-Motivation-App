from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import Student, db
from flask_cors import cross_origin
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

student_bp = Blueprint('student', __name__)

# ✅ Student Login Route (Fixing Missing Route)
@student_bp.route('/student/login', methods=['POST'])
@cross_origin(origin="http://localhost:5173", "https://motiviationapp-d4cm.vercel.app", supports_credentials=True)  # ✅ Allow frontend requests
def student_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    student = Student.query.filter_by(email=email).first()
    if not student or not check_password_hash(student.password, password):
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    access_token = create_access_token(identity={"id": student.id, "role": "student"})
    return jsonify({"success": True, "access_token": access_token, "role": "student"}), 200

# ✅ Create a new student
@student_bp.route('/students', methods=['POST'])
@cross_origin(origin="http://localhost:5173", "https://motiviationapp-d4cm.vercel.app", supports_credentials=True)
def create_student():
    try:
        data = request.get_json()
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')

        if not email or not username or not password:
            return jsonify({"message": "Email, username, and password are required"}), 400

        if Student.query.filter_by(email=email).first():
            return jsonify({"message": "Email already exists"}), 400
        if Student.query.filter_by(username=username).first():
            return jsonify({"message": "Username already exists"}), 400

        hashed_password = generate_password_hash(password)

        new_student = Student(email=email, username=username, password=hashed_password)
        db.session.add(new_student)
        db.session.commit()

        logger.info(f"Student created successfully with ID: {new_student.id}")
        return jsonify({"message": "Student created successfully", "student_id": new_student.id}), 201

    except Exception as e:
        logger.error(f"Error creating student: {e}")
        return jsonify({"message": "An error occurred while creating the student"}), 500

# ✅ Get all students
@student_bp.route('/students', methods=['GET'])
@cross_origin(origin="http://localhost:5173", "https://motiviationapp-d4cm.vercel.app", supports_credentials=True)
@jwt_required()
def get_students():
    try:
        students = Student.query.all()
        students_data = [{
            "id": student.id,
            "email": student.email,
            "username": student.username,
            "created_at": student.created_at.isoformat()
        } for student in students]
        return jsonify(students_data), 200

    except Exception as e:
        logger.error(f"Error retrieving students: {e}")
        return jsonify({"message": "An error occurred while retrieving students"}), 500

# ✅ Get a specific student by ID (Fixed Route Name)
@student_bp.route('/students/<int:student_id>', methods=['GET'])
@cross_origin(origin="http://localhost:5173", "https://motiviationapp-d4cm.vercel.app", supports_credentials=True)
@jwt_required()
def get_student(student_id):
    try:
        student = Student.query.get_or_404(student_id)
        student_data = {
            "id": student.id,
            "email": student.email,
            "username": student.username,
            "created_at": student.created_at.isoformat()
        }
        return jsonify(student_data), 200

    except Exception as e:
        logger.error(f"Error retrieving student with ID {student_id}: {e}")
        return jsonify({"message": "An error occurred while retrieving the student"}), 500

# ✅ Update a student (Fixed Route Name)
@student_bp.route('/students/<int:student_id>', methods=['PUT'])
@cross_origin(origin="http://localhost:5173", "https://motiviationapp-d4cm.vercel.app", supports_credentials=True)
@jwt_required()
def update_student(student_id):
    try:
        data = request.get_json()
        student = Student.query.get_or_404(student_id)

        if 'email' in data:
            new_email = data['email']
            if Student.query.filter(Student.email == new_email, Student.id != student_id).first():
                return jsonify({"message": "Email already exists"}), 400
            student.email = new_email

        if 'username' in data:
            new_username = data['username']
            if Student.query.filter(Student.username == new_username, Student.id != student_id).first():
                return jsonify({"message": "Username already exists"}), 400
            student.username = new_username

        if 'password' in data:
            new_password = data['password']
            student.password = generate_password_hash(new_password)

        db.session.commit()
        logger.info(f"Student with ID {student_id} updated successfully")
        return jsonify({"message": "Student updated successfully"}), 200

    except Exception as e:
        logger.error(f"Error updating student with ID {student_id}: {e}")
        return jsonify({"message": "An error occurred while updating the student"}), 500

# ✅ Delete a student (Fixed Route Name)
@student_bp.route('/students/<int:student_id>', methods=['DELETE'])
@cross_origin(origin="http://localhost:5173", "https://motiviationapp-d4cm.vercel.app", supports_credentials=True)
def delete_student(student_id):
    try:
        student = Student.query.get_or_404(student_id)
        db.session.delete(student)
        db.session.commit()
        logger.info(f"Student with ID {student_id} deleted successfully")
        return jsonify({"message": "Student deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting student with ID {student_id}: {e}")
        return jsonify({"message": "An error occurred while deleting the student"}), 500
