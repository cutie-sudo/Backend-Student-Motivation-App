import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from models import db, Admin, Student

profile_bp = Blueprint("profile_bp", __name__)

# Configure allowed file types and upload folder.
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@profile_bp.route("/profile", methods=["GET", "PUT"])
@jwt_required()
def handle_profile():
    """
    GET  /profile  -> returns the logged-in user's info (including profile_pic)
    PUT  /profile  -> updates the user's username, email, or password
    """
    try:
        # Verify the JWT token and get the current user's identity.
        verify_jwt_in_request()
        current_user_data = get_jwt_identity()
        role = current_user_data.get("role")
        user_id = current_user_data.get("id")

        if not role or not user_id:
            return jsonify({"success": False, "error": "Invalid token: missing role or ID"}), 401

        # Retrieve user from DB based on role.
        if role == "admin":
            user = Admin.query.get(user_id)
        else:
            user = Student.query.get(user_id)

        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        if request.method == "GET":
            return jsonify({
                "success": True,
                "data": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": role,
                    "profile_pic": user.profile_pic  # Include profile picture info.
                }
            }), 200

        elif request.method == "PUT":
            data = request.get_json()
            new_username = data.get("username")
            new_email = data.get("email")
            new_password = data.get("password")  # Optional

            if new_username:
                user.username = new_username
            if new_email:
                user.email = new_email
            if new_password:
                user.password = generate_password_hash(new_password)

            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Profile updated successfully!"
            }), 200

    except Exception as e:
        # Log the error for debugging.
        current_app.logger.error(f"Error in /profile: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@profile_bp.route("/profile/picture", methods=["POST"])
@jwt_required()
def update_profile_picture():
    """
    POST /profile/picture -> Updates the user's profile picture.
    Expects a multipart/form-data request with a file input named 'file'.
    """
    try:
        current_user_data = get_jwt_identity()
        role = current_user_data.get("role")
        user_id = current_user_data.get("id")

        if role == "admin":
            user = Admin.query.get(user_id)
        else:
            user = Student.query.get(user_id)

        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file part in the request"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"success": False, "error": "No selected file"}), 400

        if file and allowed_file(file.filename):
            # Ensure the upload folder exists.
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            # Update the user's profile picture.
            user.profile_pic = filename
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Profile picture updated successfully!",
                "profile_pic": filename
            }), 200

        return jsonify({"success": False, "error": "File type not allowed"}), 400

    except Exception as e:
        # Log the error for debugging.
        current_app.logger.error(f"Error in /profile/picture: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@profile_bp.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)