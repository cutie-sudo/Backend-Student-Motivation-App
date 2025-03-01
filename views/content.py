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
    content_type = data.get('content_type')  # 'video', 'note', 'podcast'
    content_link = data.get('content_link')  # e.g., YouTube link for videos

    current_user = get_jwt_identity()
    admin_id = current_user.get("id")
    role = current_user.get("role")

    # Ensure the user is an admin
    if role != "admin":
        return jsonify({"message": "Only admins can add content"}), 403

    # Validation
    if not title or not category_id or not content_type:
        return jsonify({"message": "Title, category ID, and content type are required"}), 400

    if content_type in ['video', 'podcast'] and not content_link:
        return jsonify({"message": "Content link is required for videos and podcasts"}), 400

    if content_type == 'note' and not description:
        return jsonify({"message": "Description is required for notes"}), 400

    # Check if the category exists
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"message": "Category not found"}), 404

    # Create and save the new content
    new_content = Content(
        title=title,
        description=description,
        category_id=category_id,
        status='pending',
        admin_id=admin_id,
        content_type=content_type,
        content_link=content_link
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
        "admin_id": content.admin_id,
        "content_type": content.content_type,
        "content_link": content.content_link
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
        "admin_id": content.admin_id,
        "content_type": content.content_type,
        "content_link": content.content_link
    }
    
    return jsonify(content_data), 200
