from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
from models import Student, db, Post, Wishlist

wishlist_bp = Blueprint('wishlist', __name__)

# Allowed origins for CORS
ALLOWED_ORIGINS = ["https://students-motiviation-app-vkmx.vercel.app"]

@wishlist_bp.route('/wishlist', methods=['POST'])
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
@jwt_required()
def add_to_wishlist():
    student = get_jwt_identity()
    student_id = student["id"]
    data = request.get_json()
    post_id = data.get('post_id')

    if not post_id:
        return jsonify({"message": "Post ID is required"}), 400

    post = Post.query.get(post_id)
    if not post:
        return jsonify({"message": "Post not found"}), 404

    existing_item = Wishlist.query.filter_by(student_id=student_id, post_id=post_id).first()
    if existing_item:
        return jsonify({"message": "Already in wishlist"}), 400

    wishlist_item = Wishlist(student_id=student_id, post_id=post_id)
    db.session.add(wishlist_item)
    db.session.commit()

    return jsonify({"message": "Added to wishlist successfully", "wishlist_id": wishlist_item.id}), 201

@wishlist_bp.route('/wishlist', methods=['GET'])
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
@jwt_required()
def get_wishlist():
    student = get_jwt_identity()
    student_id = student["id"]
    wishlist_items = Wishlist.query.filter_by(student_id=student_id).all()

    wishlist_data = [
        {
            "wishlist_id": item.id,
            "post_id": item.post.id,
            "title": item.post.title,
            "content": item.post.content,
            "category_id": item.post.category_id,
            "admin_id": item.post.admin_id,
            "student_id": item.post.student_id,
            "created_at": item.post.created_at,
            "is_approved": item.post.is_approved,
            "is_flagged": item.post.is_flagged,
            "likes": item.post.likes,
            "dislikes": item.post.dislikes
        }
        for item in wishlist_items if item.post
    ]

    return jsonify(wishlist_data), 200

@wishlist_bp.route('/wishlist/<int:wishlist_id>', methods=['DELETE'])
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
@jwt_required()
def remove_from_wishlist(wishlist_id):
    student = get_jwt_identity()
    student_id = student["id"]
    wishlist_item = Wishlist.query.get_or_404(wishlist_id)

    if wishlist_item.student_id != student_id:
        return jsonify({"message": "Unauthorized"}), 403

    db.session.delete(wishlist_item)
    db.session.commit()
    return jsonify({"message": "Removed from wishlist successfully"}), 200
