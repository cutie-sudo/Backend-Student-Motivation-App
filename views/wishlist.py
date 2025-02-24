from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Student, db, Post, Wishlist


wishlist_bp = Blueprint('wishlist', __name__)


@wishlist_bp.route('/wishlist', methods=['POST'])
@jwt_required()
def add_to_wishlist():
    student_id = get_jwt_identity()  # Get logged-in student's ID
    data = request.get_json()
    post_id = data.get('post_id')

    # Validate input
    if not post_id:
        return jsonify({"message": "Post ID is required"}), 400

    # Check if the post exists
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"message": "Post not found"}), 404

    # Check if already in wishlist
    existing_item = Wishlist.query.filter_by(
        student_id=student_id,
        post_id=post_id
    ).first()
    
    if existing_item:
        return jsonify({"message": "Already in wishlist"}), 400

    # Add to wishlist
    wishlist_item = Wishlist(student_id=student_id, post_id=post_id)
    db.session.add(wishlist_item)
    db.session.commit()

    return jsonify({"message": "Added to wishlist successfully", "wishlist_id": wishlist_item.id}), 201

@wishlist_bp.route('/wishlist', methods=['GET'])
@jwt_required()
def get_wishlist():
    student_id = get_jwt_identity()
    wishlist_items = Wishlist.query.filter_by(student_id=student_id).all()
    
    return jsonify([{
        "wishlist_id": item.id,
        "post_id": item.post_id
    } for item in wishlist_items]), 200

@wishlist_bp.route('/wishlist/<int:wishlist_id>', methods=['DELETE'])
@jwt_required()
def remove_from_wishlist(wishlist_id):
    student_id = get_jwt_identity()
    wishlist_item = Wishlist.query.get_or_404(wishlist_id)
    
    if wishlist_item.student_id != student_id:
        return jsonify({"message": "Unauthorized"}), 403
        
    db.session.delete(wishlist_item)
    db.session.commit()
    return jsonify({"message": "Removed from wishlist successfully"}), 200