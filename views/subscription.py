from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Subscription, Category, db

subscription_bp = Blueprint('subscription', __name__)

@subscription_bp.route('/subscriptions', methods=['POST'])
@jwt_required()
def subscribe():
    student_id = get_jwt_identity()  # Get logged-in student ID
    data = request.get_json()
    category_id = data.get('category_id')

    # Validate input
    if not category_id:
        return jsonify({"message": "Category ID is required"}), 400

    # Check if the category exists
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"message": "Category not found"}), 404

    # Check if already subscribed
    existing_sub = Subscription.query.filter_by(
        student_id=student_id, 
        category_id=category_id
    ).first()
    
    if existing_sub:
        return jsonify({"message": "Already subscribed"}), 400

    # Add new subscription
    subscription = Subscription(student_id=student_id, category_id=category_id)
    db.session.add(subscription)
    db.session.commit()

    return jsonify({"message": "Subscribed successfully", "subscription_id": subscription.id}), 201


@subscription_bp.route('/subscriptions', methods=['GET'])
@jwt_required()
def get_subscriptions():
    student_id = get_jwt_identity()
    subscriptions = Subscription.query.filter_by(student_id=student_id).all()
    return jsonify([{
        "subscription_id": sub.id,
        "category_id": sub.category_id
    } for sub in subscriptions]), 200

@subscription_bp.route('/subscriptions/<int:subscription_id>', methods=['DELETE'])
@jwt_required()
def unsubscribe(subscription_id):
    student_id = get_jwt_identity()
    subscription = Subscription.query.get_or_404(subscription_id)
    
    if subscription.student_id != student_id:
        return jsonify({"message": "Unauthorized"}), 403
        
    db.session.delete(subscription)
    db.session.commit()
    return jsonify({"message": "Unsubscribed successfully"}), 200
