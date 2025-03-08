from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import UserPreference, db
from flask_cors import cross_origin


preference_bp = Blueprint('preference', __name__)


@preference_bp.route('/preferences', methods=['POST'])
@cross_origin(origins="*", supports_credentials=True)
@jwt_required()

def add_preference():
    student_id = get_jwt_identity()
    data = request.get_json()
    pref_type = data.get('preference_type')
    pref_value = data.get('preference_value')

    # Validate input
    if not pref_type or not pref_value:
        return jsonify({"message": "Preference type and value are required"}), 400

    # Check if the preference already exists
    existing_pref = UserPreference.query.filter_by(
        student_id=student_id,
        preference_type=pref_type,
        preference_value=pref_value
    ).first()
    
    if existing_pref:
        return jsonify({"message": "Preference already exists"}), 400

    # Add new preference
    preference = UserPreference(
        student_id=student_id,
        preference_type=pref_type,
        preference_value=pref_value
    )
    db.session.add(preference)
    db.session.commit()

    return jsonify({"message": "Preference added successfully", "preference_id": preference.id}), 201
    
@preference_bp.route('/preferences', methods=['GET'])
@cross_origin(origins="*", supports_credentials=True)
@jwt_required()

def get_preferences():
    student_id = get_jwt_identity()
    preferences = UserPreference.query.filter_by(student_id=student_id).all()
    
    return jsonify([{
        "type": pref.preference_type,
        "value": pref.preference_value
    } for pref in preferences]), 200
