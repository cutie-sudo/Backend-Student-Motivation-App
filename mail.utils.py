from flask_mail import Mail, Message
from flask import url_for
from itsdangerous import URLSafeTimedSerializer
from config import Config

mail = Mail()
serializer = URLSafeTimedSerializer(Config.SECRET_KEY)

def generate_reset_token(email):
    return serializer.dumps(email, salt="password-reset")

def send_reset_email(user):
    token = generate_reset_token(user.email)
    reset_link = url_for('reset_password', token=token, _external=True)

    msg = Message("Password Reset Request", recipients=[user.email])
    msg.body = f"Click the link to reset your password: {reset_link}\n\nThis link will expire in 1 hour."

    mail.send(msg)