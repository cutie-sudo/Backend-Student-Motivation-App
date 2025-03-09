import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Content, Category, db
from flask_cors import cross_origin

# Define Blueprint
content_bp = Blueprint('content', __name__)

# Helper function to get content by ID
def get_content_by_id(content_id):
    content = Content.query.get(content_id)
    if not content:
        return None
    return content

# Route to add content
@content_bp.route('/content', methods=['POST'])
@cross_origin(origins="*", supports_credentials=True)
@jwt_required()
def add_content():
    data = request.get_json()
    title, description = data.get('title'), data.get('description')
    category_id, content_type = data.get('category_id'), data.get('content_type')
    content_link = data.get('content_link')
    
    current_user = get_jwt_identity()
    if not current_user or current_user.get("role") != "admin":
        return jsonify({"message": "Only admins can add content"}), 403

    if not title or not category_id or not content_type:
        return jsonify({"message": "Title, category ID, and content type are required"}), 400

    if content_type in ['video', 'podcast'] and not content_link:
        return jsonify({"message": "Content link is required for videos and podcasts"}), 400

    if content_type == 'note' and not description:
        return jsonify({"message": "Description is required for notes"}), 400

    category = Category.query.get(category_id)
    if not category:
        return jsonify({"message": "Category not found"}), 404

    new_content = Content(
        title=title, description=description, category_id=category_id,
        status='pending', admin_id=current_user.get("id"),
        content_type=content_type, content_link=content_link
    )
    db.session.add(new_content)
    db.session.commit()

    return jsonify({"message": "Content added successfully", "content_id": new_content.id}), 201

# Route to get all content
@content_bp.route('/content', methods=['GET'])
@cross_origin(origins="*", supports_credentials=True)
def get_all_content():
    content_list = Content.query.all()
    return jsonify([{ "id": c.id, "title": c.title, "description": c.description,
                      "category_id": c.category_id, "status": c.status, "admin_id": c.admin_id,
                      "content_type": c.content_type, "content_link": c.content_link} for c in content_list]), 200

# Route to get specific content by ID
@content_bp.route('/content/<int:content_id>', methods=['GET'])
@cross_origin(origins="*", supports_credentials=True)
@jwt_required()
def get_content(content_id):
    content = get_content_by_id(content_id)
    if not content:
        return jsonify({"message": "Content not found"}), 404
    return jsonify({ "id": content.id, "title": content.title, "description": content.description,
                     "category_id": content.category_id, "status": content.status,
                     "admin_id": content.admin_id, "content_type": content.content_type,
                     "content_link": content.content_link }), 200

# Route to like/dislike content
@content_bp.route('/content/<int:content_id>/<action>', methods=['POST'])
@cross_origin(origins="*", supports_credentials=True)
@jwt_required()
def react_to_content(content_id, action):
    content = get_content_by_id(content_id)
    if not content:
        return jsonify({"message": "Content not found"}), 404
    
    if action == "like":
        content.likes = getattr(content, 'likes', 0) + 1
    elif action == "dislike":
        content.dislikes = getattr(content, 'dislikes', 0) + 1
    else:
        return jsonify({"message": "Invalid action"}), 400
    
    db.session.commit()
    return jsonify({"message": f"Content {action}d successfully"}), 200

# Route to flag content
@content_bp.route('/content/<int:content_id>/flag', methods=['POST'])
@cross_origin(origins="*", supports_credentials=True)
@jwt_required()
def flag_content(content_id):
    content = get_content_by_id(content_id)
    if not content:
        return jsonify({"message": "Content not found"}), 404
    
    content.is_flagged = True
    db.session.commit()
    return jsonify({"message": "Content flagged successfully"}), 200

# Route to approve content
@content_bp.route('/content/<int:content_id>/approve', methods=['PATCH'])
@cross_origin(origins="*", supports_credentials=True)
@jwt_required()
def approve_content(content_id):
    content = get_content_by_id(content_id)
    if not content:
        return jsonify({"message": "Content not found"}), 404
    
    content.is_approved = True
    db.session.commit()
    return jsonify({"message": "Content approved successfully"}), 200

# Route to delete content
@content_bp.route('/content/<int:content_id>', methods=['DELETE'])
@cross_origin(origins="*", supports_credentials=True)
@jwt_required()
def delete_content(content_id):
    content = get_content_by_id(content_id)
    if not content:
        return jsonify({"message": "Content not found"}), 404
    
    db.session.delete(content)
    db.session.commit()
    return jsonify({"message": "Content removed successfully"}), 200

# Route to edit content
@content_bp.route('/content/<int:content_id>', methods=['PUT'])
@cross_origin(origins="*", supports_credentials=True)
@jwt_required()
def edit_content(content_id):
    content = get_content_by_id(content_id)
    if not content:
        return jsonify({"message": "Content not found"}), 404
    
    data = request.get_json()
    for field in ["title", "description", "content_link", "content_type", "category_id"]:
        if field in data:
            setattr(content, field, data[field])
    db.session.commit()
    
    return jsonify({"message": "Content updated successfully"}), 200
