from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin

subscription_bp = Blueprint('subscription', __name__)

# ✅ Delayed import to avoid circular imports
def get_models():
    from models import Subscription, Category, db
    return Subscription, Category, db


@subscription_bp.route('/subscriptions', methods=['POST'])
@cross_origin(origin="http://localhost:5173", "https://motiviationapp-d4cm.vercel.app" supports_credentials=True)
@jwt_required()
def subscribe():
    Subscription, Category, db = get_models()  # Import models inside function
    student_id = get_jwt_identity()
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
        student_id=student_id, category_id=category_id
    ).first()

    if existing_sub:
        return jsonify({"message": "Already subscribed"}), 400

    # Add new subscription
    subscription = Subscription(student_id=student_id, category_id=category_id)
    db.session.add(subscription)
    db.session.commit()

    return jsonify({
        "message": "Subscribed successfully",
        "subscription_id": subscription.id
    }), 201


@subscription_bp.route('/subscriptions', methods=['GET'])
@cross_origin(origin="http://localhost:5173", "https://motiviationapp-d4cm.vercel.app" supports_credentials=True)
@jwt_required()
def get_subscriptions():
    Subscription, _, _ = get_models()  # Import models inside function
    student_id = get_jwt_identity()
    
    subscriptions = Subscription.query.filter_by(student_id=student_id).all()
    return jsonify([{
        "subscription_id": sub.id,
        "category_id": sub.category_id
    } for sub in subscriptions]), 200


@subscription_bp.route('/subscriptions/<int:subscription_id>', methods=['DELETE'])
@cross_origin(origin="http://localhost:5173", "https://motiviationapp-d4cm.vercel.app" supports_credentials=True)
@jwt_required()
def unsubscribe(subscription_id):
    Subscription, _, db = get_models()  # Import models inside function
    student_id = get_jwt_identity()
    
    subscription = Subscription.query.get(subscription_id)
    
    if not subscription:
        return jsonify({"message": "Subscription not found"}), 404
    
    if subscription.student_id != student_id:
        return jsonify({"message": "Unauthorized"}), 403

    db.session.delete(subscription)
    db.session.commit()

    return jsonify({"message": "Unsubscribed successfully"}), 200
