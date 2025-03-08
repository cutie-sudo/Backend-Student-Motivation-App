import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models import Admin, Student, Category, db  # Ensure all required models are imported
from flask_cors import cross_origin

admin_bp = Blueprint('admin', __name__)

# -------------------------
# Admin Login Route
# -------------------------
@admin_bp.route('/admin/login', methods=['POST'])
@cross_origin(origins=["https://students-motiviation-app-vkmx.vercel.app"], supports_credentials=True)
def admin_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    admin = Admin.query.filter_by(email=email).first()
    if not admin or not check_password_hash(admin.password, password):
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    access_token = create_access_token(identity={"id": admin.id, "role": "admin"})
    return jsonify({"success": True, "access_token": access_token, "role": "admin"}), 200

# -------------------------
# Create a New Admin
# -------------------------
@admin_bp.route('/admins', methods=['POST'])
@cross_origin(origins=["https://students-motiviation-app-vkmx.vercel.app"], supports_credentials=True)
@jwt_required()  # Only allow authenticated users to create admins
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

# -------------------------
# Get All Admins
# -------------------------
@admin_bp.route('/admins', methods=['GET'])
@cross_origin(origins=["https://students-motiviation-app-vkmx.vercel.app"], supports_credentials=True) 
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

# -------------------------
# Get a Specific Admin by ID
# -------------------------
@admin_bp.route('/admins/<int:admin_id>', methods=['GET'])
@cross_origin(origins=["https://students-motiviation-app-vkmx.vercel.app"], supports_credentials=True)  
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

# -------------------------
# Update an Admin
# -------------------------
@admin_bp.route('/admins/<int:admin_id>', methods=['PUT'])
@cross_origin(origins=["https://students-motiviation-app-vkmx.vercel.app"], supports_credentials=True)  
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

# -------------------------
# Delete an Admin
# -------------------------
@admin_bp.route('/admins/<int:admin_id>', methods=['DELETE'])
@cross_origin(origins=["https://students-motiviation-app-vkmx.vercel.app"], supports_credentials=True)  
@jwt_required()
def delete_admin(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    db.session.delete(admin)
    db.session.commit()
    return jsonify({"message": "Admin deleted successfully"}), 200

# -------------------------
# Deactivate a User (Student or Admin)
# -------------------------
@admin_bp.route('/users/<int:user_id>/deactivate', methods=['PATCH'])
@cross_origin(origins=["https://students-motiviation-app-vkmx.vercel.app"], supports_credentials=True)
@jwt_required()
def deactivate_user(user_id):
    # First try to find as a Student; if not found, try Admin.
    user = Student.query.get(user_id) or Admin.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    user.is_active = False
    db.session.commit()
    return jsonify({"message": "User deactivated successfully"}), 200

# -------------------------
# Delete a Category
# -------------------------
@admin_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@cross_origin(origins=["https://students-motiviation-app-vkmx.vercel.app"], supports_credentials=True)
@jwt_required()
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Category deleted successfully"}), 200