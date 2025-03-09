from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Category, db
from flask_cors import cross_origin

category_bp = Blueprint('category', __name__)

# Helper function to get category by ID
def get_category_by_id(category_id):
    return Category.query.get(category_id)

# Add a new category
@category_bp.route('/categories', methods=['POST'])
@cross_origin(origins="*", supports_credentials=True)
@jwt_required()
def add_category():
    data = request.get_json()
    name = data.get('name')
    
    current_user = get_jwt_identity()
    if current_user.get("role") != "admin":
        return jsonify({"message": "Only admins can add categories"}), 403

    if not name:
        return jsonify({"message": "Category name is required"}), 400

    if Category.query.filter_by(name=name).first():
        return jsonify({"message": "Category already exists"}), 400

    new_category = Category(name=name, admin_id=current_user.get("id"))
    db.session.add(new_category)
    db.session.commit()

    return jsonify({"message": "Category added successfully", "category_id": new_category.id}), 201

# Get all categories
@category_bp.route('/categories', methods=['GET'])
@cross_origin(origins="*", supports_credentials=True)
def get_categories():
    categories = Category.query.all()
    return jsonify([{ "id": c.id, "name": c.name, "admin_id": c.admin_id } for c in categories]), 200

# Update a category
@category_bp.route('/categories/<int:category_id>', methods=['PUT'])
@cross_origin(origins="*", supports_credentials=True)
@jwt_required()
def update_category(category_id):
    data = request.get_json()
    new_name = data.get('name')
    
    current_user = get_jwt_identity()
    category = get_category_by_id(category_id)
    
    if not category:
        return jsonify({"message": "Category not found"}), 404
    
    if current_user.get("role") != "admin":
        return jsonify({"message": "Only admins can update categories"}), 403

    if category.admin_id != current_user.get("id"):
        return jsonify({"message": "Unauthorized: You can only update categories you created"}), 403

    if not new_name:
        return jsonify({"message": "New category name is required"}), 400

    if Category.query.filter_by(name=new_name).first():
        return jsonify({"message": "Category name already exists"}), 400

    category.name = new_name
    db.session.commit()
    return jsonify({"message": "Category updated successfully", "category_id": category.id}), 200

# Delete a category
@category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@cross_origin(origins="*", supports_credentials=True)
@jwt_required()
def delete_category(category_id):
    current_user = get_jwt_identity()
    category = get_category_by_id(category_id)
    
    if not category:
        return jsonify({"message": "Category not found"}), 404
    
    if current_user.get("role") != "admin":
        return jsonify({"message": "Only admins can delete categories"}), 403

    if category.admin_id != current_user.get("id"):
        return jsonify({"message": "Unauthorized: You can only delete categories you created"}), 403

    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Category deleted successfully"}), 200
