from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from models import Admin
from models import db
from flask_cors import cross_origin



admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admins', methods=['POST'])
def create_admin():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if not email or not username or not password:
        return jsonify({"message": "Email, username, and password are required"}), 400

    
    if Admin.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 400
    if Admin.query.filter_by(username=username).first():
        return jsonify({"message": "Username already exists"}), 400

    
    hashed_password = generate_password_hash(password)

    
    new_admin = Admin(email=email, username=username, password=hashed_password)
    db.session.add(new_admin)
    db.session.commit()

    return jsonify({"message": "Admin created successfully", "admin_id": new_admin.id}), 201


@admin_bp.route('/admins', methods=['GET'])
@cross_origin(origin="http://localhost:5173", supports_credentials=True) 
@jwt_required()

@jwt_required()
def get_admins():
    admins = Admin.query.all()
    admins_data = [{
        "id": admin.id,
        "email": admin.email,
        "username": admin.username,
        "created_at": admin.created_at.isoformat()
    } for admin in admins]
    return jsonify(admins_data), 200


@admin_bp.route('/<int:admin_id>', methods=['GET'])
@cross_origin(origin="http://localhost:5173", supports_credentials=True)  
@jwt_required()
def get_admin(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    admin_data = {
        "id": admin.id,
        "email": admin.email,
        "username": admin.username,
        "created_at": admin.created_at.isoformat()
    }
    return jsonify(admin_data), 200


@admin_bp.route('/<int:admin_id>', methods=['PUT'])
@cross_origin(origin="http://localhost:5173", supports_credentials=True)  
@jwt_required()
def update_admin(admin_id):
    data = request.get_json()
    admin = Admin.query.get_or_404(admin_id)

    if 'email' in data:
        new_email = data['email']
        if Admin.query.filter_by(email=new_email).first():
            return jsonify({"message": "Email already exists"}), 400
        admin.email = new_email

    if 'username' in data:
        new_username = data['username']
        if Admin.query.filter_by(username=new_username).first():
            return jsonify({"message": "Username already exists"}), 400
        admin.username = new_username

    if 'password' in data:
        new_password = data['password']
        admin.password = generate_password_hash(new_password)

    db.session.commit()
    return jsonify({"message": "Admin updated successfully"}), 200


@admin_bp.route('/<int:admin_id>', methods=['DELETE'])
@cross_origin(origin="http://localhost:5173", supports_credentials=True)  
@jwt_required()
def delete_admin(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    db.session.delete(admin)
    db.session.commit()
    return jsonify({"message": "Admin deleted successfully"}), 200
