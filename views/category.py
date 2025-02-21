from flask import Flask, request, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, decode_token  # Import decode_token if needed
from sqlalchemy.exc import IntegrityError
from models import Category  # Or from models import Category, depending on your structure
from app import db


category_bp = Blueprint('category', __name__)
@category_bp.route('/categories', methods=['POST'])
@jwt_required()
def add_category():
    data = request.get_json()
    name = data.get('name')
    admin_id = get_jwt_identity()

    if not name:
        return jsonify({"message": "Category name is required"}), 400

    # Check if the category already exists
    if Category.query.filter_by(name=name).first():
        return jsonify({"message": "Category already exists"}), 400

    new_category = Category(name=name, admin_id=admin_id)
    db.session.add(new_category)
    db.session.commit()

    return jsonify({"message": "Category added successfully", "category_id": new_category.id}), 201

@category_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    categories_data = [{"id": category.id, "name": category.name, "admin_id": category.admin_id} for category in categories]
    return jsonify(categories_data), 200


@category_bp.route('/categories/<int:category_id>', methods=['PUT'])
@jwt_required()
def update_category(category_id):
    data = request.get_json()
    new_name = data.get('name')  # New name for the category
    admin_id = get_jwt_identity()  # Get the admin ID from the JWT token

    # Check if the category exists
    category = Category.query.get_or_404(category_id)

    # Ensure the admin updating the category is the one who created it
    if category.admin_id != admin_id:
        return jsonify({"message": "Unauthorized: You can only update categories you created"}), 403

    # Check if the new name is provided
    if not new_name:
        return jsonify({"message": "New category name is required"}), 400

    # Check if the new name already exists (to avoid duplicates)
    existing_category = Category.query.filter_by(name=new_name).first()
    if existing_category and existing_category.id != category_id:
        return jsonify({"message": "Category name already exists"}), 400

    # Update the category name
    category.name = new_name
    db.session.commit()

    return jsonify({"message": "Category updated successfully", "category_id": category.id}), 200

@category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    admin_id = get_jwt_identity()
    category = Category.query.get_or_404(category_id)

    if category.admin_id != admin_id:
        return jsonify({"message": "Unauthorized"}), 403

    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Category deleted successfully"}), 200