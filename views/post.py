from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Post, db, Student
from flask_cors import cross_origin

post_bp = Blueprint('post', __name__)

# ✅ Create a new post
@post_bp.route('/posts', methods=['POST'])
@cross_origin(origin="*", supports_credentials=True)
@jwt_required()
def add_post():
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    category_id = data.get('category_id')

    if not title or not content or not category_id:
        return jsonify({"message": "Title, content, and category ID are required"}), 400

    user_id = get_jwt_identity()  # JWT returns user ID
    student = Student.query.get(user_id)

    if not student:
        return jsonify({"message": "Unauthorized user"}), 403

    new_post = Post(
        title=title,
        content=content,
        category_id=int(category_id),  # Ensure it's an integer
        student_id=user_id,
    )

    db.session.add(new_post)
    db.session.commit()

    return jsonify({"message": "Post added successfully", "post_id": new_post.id}), 201


# ✅ Get all posts
@post_bp.route('/posts', methods=['GET'])
@cross_origin(origin="*", supports_credentials=True)
def get_posts():
    posts = Post.query.all()
    posts_data = [
        {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "category_id": post.category_id,
            "student_id": post.student_id,
            "created_at": post.created_at.isoformat() if post.created_at else None
        }
        for post in posts
    ]
    return jsonify(posts_data), 200


# ✅ Get a specific post by ID
@post_bp.route('/post/<int:post_id>', methods=['GET'])
@cross_origin(origin="*", supports_credentials=True)
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    post_data = {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "category_id": post.category_id,
        "student_id": post.student_id,
        "created_at": post.created_at.isoformat() if post.created_at else None
    }
    return jsonify(post_data), 200


# ✅ Update a post (only if the student is the owner)
@post_bp.route('/post/<int:post_id>', methods=['PUT'])
@cross_origin(origin="*", supports_credentials=True)
@jwt_required()
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    user_id = get_jwt_identity()

    if post.student_id != user_id:
        return jsonify({"message": "Unauthorized: You can only update your own posts"}), 403

    data = request.get_json()

    if 'title' in data:
        post.title = data['title']
    if 'content' in data:
        post.content = data['content']
    if 'category_id' in data:
        post.category_id = int(data['category_id'])  # Ensure it's an integer
    if 'is_approved' in data:
        post.is_approved = bool(data['is_approved'])
    if 'is_flagged' in data:
        post.is_flagged = bool(data['is_flagged'])

    db.session.commit()
    return jsonify({"message": "Post updated successfully", "post_id": post.id}), 200


# ✅ Delete a post (only if the student is the owner)
@post_bp.route('/post/<int:post_id>', methods=['DELETE'])
@cross_origin(origin="*", supports_credentials=True)
@jwt_required()
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    user_id = get_jwt_identity()

    if post.student_id != user_id:
        return jsonify({"message": "Unauthorized: You can only delete your own posts"}), 403

    db.session.delete(post)
    db.session.commit()
    return jsonify({"message": "Post deleted successfully"}), 200


# ✅ Like a post
@post_bp.route('/post/<int:post_id>/like', methods=['POST'])
@cross_origin(origin="*", supports_credentials=True)
@jwt_required()
def like_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.likes is None:
        post.likes = 0

    post.likes += 1
    db.session.commit()
    return jsonify({"message": "Post liked successfully", "likes": post.likes}), 200


# ✅ Dislike a post
@post_bp.route('/post/<int:post_id>/dislike', methods=['POST'])
@cross_origin(origin="*", supports_credentials=True)
@jwt_required()
def dislike_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.dislikes is None:
        post.dislikes = 0

    post.dislikes += 1
    db.session.commit()
    return jsonify({"message": "Post disliked successfully", "dislikes": post.dislikes}), 200
