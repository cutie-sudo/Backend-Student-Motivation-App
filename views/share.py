from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Share, Post, Student, db
from flask_cors import cross_origin



share_bp = Blueprint('share', __name__)


@share_bp.route('/shares', methods=['POST'])
@jwt_required()
@cross_origin(origin="http://localhost:5173", supports_credentials=True)
def share_post():
    student_id = get_jwt_identity()  # The logged-in student
    data = request.get_json()
    post_id = data.get('post_id')
    shared_with_id = data.get('shared_with_id')

    # Validate required fields
    if not all([post_id, shared_with_id]):
        return jsonify({"message": "Post ID and recipient ID are required"}), 400

    # Prevent sharing with self
    if student_id == shared_with_id:
        return jsonify({"message": "You cannot share a post with yourself"}), 400

    # Check if the post exists
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"message": "Post not found"}), 404

    # Check if the recipient student exists
    recipient = Student.query.get(shared_with_id)
    if not recipient:
        return jsonify({"message": "Recipient student not found"}), 404

    # Create the share record
    share = Share(
        post_id=post_id,
        student_id=student_id,
        shared_with_id=shared_with_id
    )
    db.session.add(share)
    db.session.commit()

    return jsonify({"message": "Post shared successfully", "share_id": share.id}), 201

