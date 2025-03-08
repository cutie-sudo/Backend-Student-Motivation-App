from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin

share_bp = Blueprint('share', __name__)

# ✅ Delayed Import Fixes Circular Import Error
def get_models():
    from models import Share, Post, Student, db
    return Share, Post, Student, db


@share_bp.route('/shares', methods=['POST'])
@jwt_required()
@cross_origin(origins="*", supports_credentials=True)
def share_post():
    Share, Post, Student, db = get_models()  # Import models inside function

    student_id = get_jwt_identity()  # The logged-in student
    data = request.get_json()
    post_id = data.get('post_id')
    shared_with = data.get('shared_with_id')  # Ensure naming matches the Share model

    # Validate required fields
    if not post_id or not shared_with:
        return jsonify({"message": "Post ID and recipient ID are required"}), 400

    # Prevent sharing with self
    if student_id == shared_with:
        return jsonify({"message": "You cannot share a post with yourself"}), 400

    # Check if the post exists
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"message": "Post not found"}), 404

    # Check if the recipient student exists
    recipient = Student.query.get(shared_with)
    if not recipient:
        return jsonify({"message": "Recipient student not found"}), 404

    # Create the share record
    share = Share(
        post_id=post_id,
        student_id=student_id,
        shared_with=shared_with  # Ensure this field matches the Share model
    )
    db.session.add(share)
    db.session.commit()

    return jsonify({"message": "Post shared successfully", "share_id": share.id}), 201
