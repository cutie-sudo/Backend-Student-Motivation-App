from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
def get_models():
    from models import Notification, db, Student
    return Notification, db, Student
from flask_cors import cross_origin



notification_bp = Blueprint('notification', __name__)


@notification_bp.route("/notifications/<int:user_id>", methods=["GET"])

@cross_origin(origin="http://localhost:5173", supports_credentials=True)
@jwt_required()
def get_notifications(user_id):

    notifications = Notification.query.filter_by(student_id=user_id).all()
    if not notifications:
        return jsonify({"message": "No notifications found"}), 404
    
    notifications_data = [
        {
            "id": n.id,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
        }
        for n in notifications
    ]
    return jsonify(notifications_data), 200


# Mark a notification as read
@notification_bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])

@cross_origin(origin="http://localhost:5173", supports_credentials=True)
@jwt_required()
def mark_notification_read(notification_id):
    student_id = get_jwt_identity()
    
    notification = Notification.query.filter_by(id=notification_id, student_id=student_id).first()

    if not notification:
        return jsonify({"message": "Notification not found"}), 404  

    if notification.is_read:
        return jsonify({"message": "Notification already marked as read"}), 200

    notification.is_read = True
    db.session.commit()
    return jsonify({"message": "Notification marked as read"}), 200
