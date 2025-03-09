from datetime import datetime
from flask import request, jsonify, Blueprint
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Comment
from flask_cors import cross_origin

comment_bp = Blueprint('comment', __name__)

# Helper function to get comment by ID
def get_comment_by_id(comment_id):
    return Comment.query.get_or_404(comment_id)

# Add a new comment
@comment_bp.route('/comments', methods=['POST'])
@cross_origin(origins="*", supports_credentials=True)
@jwt_required()
def add_comment():
    data = request.get_json()
    content, post_id = data.get('content'), data.get('post_id')
    parent_id = data.get('parent_id', None)
    student_id = get_jwt_identity().get("id")
    
    if not content or not post_id:
        return jsonify({"message": "Content and post ID are required"}), 400

    try:
        new_comment = Comment(
            content=content, student_id=student_id, post_id=post_id,
            parent_id=parent_id, created_at=datetime.utcnow()
        )
        db.session.add(new_comment)
        db.session.commit()
        return jsonify({"message": "Comment added successfully", "comment_id": new_comment.id}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Invalid student ID, post ID, or parent ID"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

# Delete a comment
@comment_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@cross_origin(origins="*", supports_credentials=True)
@jwt_required()
def delete_comment(comment_id):
    student_id = get_jwt_identity().get("id")
    comment = get_comment_by_id(comment_id)

    if comment.student_id != student_id:
        return jsonify({"message": "Unauthorized to delete this comment"}), 403

    try:
        db.session.delete(comment)
        db.session.commit()
        return jsonify({"message": "Comment deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

# Get comments for a post
@comment_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
@cross_origin(origins="*", supports_credentials=True)
def get_comments(post_id):
    comments = Comment.query.filter_by(post_id=post_id, parent_id=None).all()
    
    comments_data = [
        {
            "id": comment.id,
            "content": comment.content,
            "student_id": comment.student_id,
            "created_at": comment.created_at.isoformat(),
            "replies": [
                {
                    "id": reply.id,
                    "content": reply.content,
                    "student_id": reply.student_id,
                    "created_at": reply.created_at.isoformat(),
                    "parent_id": reply.parent_id
                } for reply in comment.replies
            ]
        } for comment in comments
    ]
    
    return jsonify(comments_data), 200

# Update a comment
@comment_bp.route('/comments/<int:comment_id>', methods=['PUT'])
@cross_origin(origins="*", supports_credentials=True)
@jwt_required()
def update_comment(comment_id):
    student_id = get_jwt_identity().get("id")
    comment = get_comment_by_id(comment_id)

    if comment.student_id != student_id:
        return jsonify({"message": "Unauthorized to update this comment"}), 403

    data = request.get_json()
    new_content = data.get('content')

    if not new_content:
        return jsonify({"message": "Content is required"}), 400

    try:
        comment.content = new_content
        db.session.commit()
        return jsonify({"message": "Comment updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500
