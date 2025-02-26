from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Content, Category
from models import db
from flask_cors import cross_origin


# Define Blueprint
content_bp = Blueprint('content', __name__)

# Route to add content
@content_bp.route('/content', methods=['POST'])

@cross_origin(origin="http://localhost:5173", supports_credentials=True)
@jwt_required()
def add_content():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    category_id = data.get('category_id')
    admin_id = get_jwt_identity()

    if not title or not description or not category_id:
        return jsonify({"message": "Title, description, and category ID are required"}), 400

    # Check if the category exists
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"message": "Category not found"}), 404

    new_content = Content(
        title=title,
        description=description,
        category_id=category_id,
        status='pending',
        admin_id=admin_id
    )
    db.session.add(new_content)
    db.session.commit()

    return jsonify({"message": "Content added successfully", "content_id": new_content.id}), 201

# Route to get all content
@content_bp.route('/content', methods=['GET'])
@cross_origin(origin="http://localhost:5173", supports_credentials=True)
def get_all_content():
    contents = Content.query.all()
    content_data = [{
        "id": content.id,
        "title": content.title,
        "description": content.description,
        "category_id": content.category_id,
        "status": content.status,
        "user_id": content.user_id
    } for content in contents]
    
    return jsonify(content_data), 200

# Route to get specific content by ID
@content_bp.route('/content/<int:content_id>', methods=['GET'])

@cross_origin(origin="http://localhost:5173", supports_credentials=True)
@jwt_required()
def get_content(content_id):
    content = Content.query.get_or_404(content_id)
    content_data = {
        "id": content.id,
        "title": content.title,
        "description": content.description,
        "category_id": content.category_id,
        "status": content.status,
        "user_id": content.user_id
    }
    
    return jsonify(content_data), 200

# Route to update content
@content_bp.route('/content/<int:content_id>', methods=['PUT'])

@cross_origin(origin="http://localhost:5173", supports_credentials=True)
@jwt_required()
def update_content(content_id):
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    status = data.get('status')
    user_id = get_jwt_identity()

    content = Content.query.get_or_404(content_id)

    # Ensure only the creator can update the content
    if content.user_id != user_id:
        return jsonify({"message": "Unauthorized: You can only update your own content"}), 403

    if title:
        content.title = title
    if description:
        content.description = description
    if status:
        content.status = status

    db.session.commit()
    return jsonify({"message": "Content updated successfully"}), 200

# Route to delete content
@content_bp.route('/content/<int:content_id>', methods=['DELETE'])
@cross_origin(origin="http://localhost:5173", supports_credentials=True)
@jwt_required()
def delete_content(content_id):
    user_id = get_jwt_identity()
    content = Content.query.get_or_404(content_id)

    # Ensure only the creator can delete the content
    if content.user_id != user_id:
        return jsonify({"message": "Unauthorized: You can only delete your own content"}), 403

    db.session.delete(content)
    db.session.commit()
    return jsonify({"message": "Content deleted successfully"}), 200
