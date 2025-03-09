from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
from models import db, Post, Wishlist

wishlist_bp = Blueprint('wishlist', __name__)

# Helper function to get wishlist item
def get_wishlist_item(wishlist_id, student_id):
    return Wishlist.query.filter_by(id=wishlist_id, student_id=student_id).first()

@wishlist_bp.route('/wishlist', methods=['POST'])
@cross_origin(origins="*", supports_credentials=True)
@jwt_required()
def add_to_wishlist():
    student_id = get_jwt_identity().get("id")
    data = request.get_json()
    post_id = data.get('post_id')

    if not post_id:
        return jsonify({"message": "Post ID is required"}), 400

    post = Post.query.get(post_id)
    if not post:
        return jsonify({"message": "Post not found"}), 404

    if Wishlist.query.filter_by(student_id=student_id, post_id=post_id).first():
        return jsonify({"message": "Already in wishlist"}), 400

    try:
        wishlist_item = Wishlist(student_id=student_id, post_id=post_id)
        db.session.add(wishlist_item)
        db.session.commit()
        return jsonify({"message": "Added to wishlist successfully", "wishlist_id": wishlist_item.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@wishlist_bp.route('/wishlist', methods=['GET'])
@cross_origin(origins="*", supports_credentials=True)
@jwt_required()
def get_wishlist():
    student_id = get_jwt_identity().get("id")

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
            "created_at": item.post.created_at.isoformat(),
            "is_approved": item.post.is_approved,
            "is_flagged": item.post.is_flagged,
            "likes": item.post.likes,
            "dislikes": item.post.dislikes
        }
        for item in wishlist_items if item.post
    ]

    return jsonify(wishlist_data), 200

@wishlist_bp.route('/wishlist/<int:wishlist_id>', methods=['DELETE'])
@cross_origin(origins="*", supports_credentials=True)
@jwt_required()
def remove_from_wishlist(wishlist_id):
    student_id = get_jwt_identity().get("id")
    wishlist_item = get_wishlist_item(wishlist_id, student_id)

    if not wishlist_item:
        return jsonify({"message": "Wishlist item not found or unauthorized"}), 404

    try:
        db.session.delete(wishlist_item)
        db.session.commit()
        return jsonify({"message": "Removed from wishlist successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500
