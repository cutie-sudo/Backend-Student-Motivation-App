from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Student, db, Post, Wishlist
from flask_cors import cross_origin

wishlist_bp = Blueprint('wishlist', __name__)

@wishlist_bp.route('/wishlist', methods=['POST'])
@cross_origin(origin="*", supports_credentials=True)
@jwt_required()
def add_to_wishlist():
    student = get_jwt_identity()  # Get logged-in student's ID
    student_id = student["id"]
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
@cross_origin(origin="*", supports_credentials=True)
@jwt_required()
def get_wishlist():
    student = get_jwt_identity()
    student_id = student["id"]
    wishlist_items = Wishlist.query.filter_by(student_id=student_id).all()
    
    wishlist_data = []
    for item in wishlist_items:
        post = Post.query.get(item.post_id)
        if post:
            wishlist_data.append({
                "wishlist_id": item.id,
                "post_id": post.id,
                "title": post.title,
                "content": post.content,
                "category_id": post.category_id,
                "admin_id": post.admin_id,
                "student_id": post.student_id,
                "created_at": post.created_at,
                "is_approved": post.is_approved,
                "is_flagged": post.is_flagged,
                "likes": post.likes,
                "dislikes": post.dislikes
            })
    
    return jsonify(wishlist_data), 200

@wishlist_bp.route('/wishlist/<int:wishlist_id>', methods=['DELETE'])
@cross_origin(origin="*", supports_credentials=True)
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