from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Category, db
from flask_cors import cross_origin

category_bp = Blueprint('category', __name__)

# Add a new category
@category_bp.route('/categories', methods=['POST'])
@cross_origin(origin="http://localhost:5173", "https://motiviationapp-d4cm.vercel.app", supports_credentials=True)
@jwt_required()
def add_category():
    data = request.get_json()
    name = data.get('name')
    
    current_user = get_jwt_identity()
    admin_id = current_user.get("id")
    role = current_user.get("role")

    # Check if the user is an admin
    if role != "admin":
        return jsonify({"message": "Only admins can add categories"}), 403

    if not name:
        return jsonify({"message": "Category name is required"}), 400

    # Check if the category already exists
    if Category.query.filter_by(name=name).first():
        return jsonify({"message": "Category already exists"}), 400

    # Create and save the new category
    new_category = Category(name=name, admin_id=admin_id)
    db.session.add(new_category)
    db.session.commit()

    return jsonify({"message": "Category added successfully", "category_id": new_category.id}), 201

# Get all categories
@category_bp.route('/categories', methods=['GET'])
@cross_origin(origin="http://localhost:5173", "https://motiviationapp-d4cm.vercel.app", supports_credentials=True)
def get_categories():
    categories = Category.query.all()
    categories_data = [{
        "id": category.id, 
        "name": category.name, 
        "admin_id": category.admin_id
    } for category in categories]
    return jsonify(categories_data), 200

# Update a category
@category_bp.route('/categories/<int:category_id>', methods=['PUT'])
@cross_origin(origin="http://localhost:5173", "https://motiviationapp-d4cm.vercel.app", supports_credentials=True)
@jwt_required()
def update_category(category_id):
    data = request.get_json()
    new_name = data.get('name')

    current_user = get_jwt_identity()
    admin_id = current_user.get("id")
    role = current_user.get("role")

    # Check if the user is an admin
    if role != "admin":
        return jsonify({"message": "Only admins can update categories"}), 403

    category = Category.query.get_or_404(category_id)

    # Ensure the admin owns the category
    if category.admin_id != admin_id:
        return jsonify({"message": "Unauthorized: You can only update categories you created"}), 403

    if not new_name:
        return jsonify({"message": "New category name is required"}), 400

    # Check for category name conflicts
    existing_category = Category.query.filter_by(name=new_name).first()
    if existing_category and existing_category.id != category_id:
        return jsonify({"message": "Category name already exists"}), 400

    category.name = new_name
    db.session.commit()

    return jsonify({"message": "Category updated successfully", "category_id": category.id}), 200

# Delete a category
@category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@cross_origin(origin="http://localhost:5173", "https://motiviationapp-d4cm.vercel.app",  supports_credentials=True)
@jwt_required()
def delete_category(category_id):
    current_user = get_jwt_identity()
    admin_id = current_user.get("id")
    role = current_user.get("role")

    # Check if the user is an admin
    if role != "admin":
        return jsonify({"message": "Only admins can delete categories"}), 403

    category = Category.query.get_or_404(category_id)

    # Ensure the admin owns the category
    if category.admin_id != admin_id:
        return jsonify({"message": "Unauthorized"}), 403

    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Category deleted successfully"}), 200
