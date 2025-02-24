from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import Student, db  


student_bp = Blueprint('student', __name__)


@student_bp.route('/students', methods=['POST'])
def create_student():
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

    return jsonify({"message": "Student created successfully", "student_id": new_student.id}), 201


@student_bp.route('/students', methods=['GET'])
@jwt_required()
def get_students():
    students = Student.query.all()
    students_data = [{
        "id": student.id,
        "email": student.email,
        "username": student.username,
        "created_at": student.created_at.isoformat()
    } for student in students]
    return jsonify(students_data), 200


@student_bp.route('/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student(student_id):
    student = Student.query.get_or_404(student_id)
    student_data = {
        "id": student.id,
        "email": student.email,
        "username": student.username,
        "created_at": student.created_at.isoformat()
    }
    return jsonify(student_data), 200


@student_bp.route('/<int:student_id>', methods=['PUT'])
@jwt_required()
def update_student(student_id):
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
    return jsonify({"message": "Student updated successfully"}), 200


@student_bp.route('/<int:student_id>', methods=['DELETE'])
@jwt_required()
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    return jsonify({"message": "Student deleted successfully"}), 200