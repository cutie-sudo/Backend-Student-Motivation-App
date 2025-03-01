from werkzeug.security import generate_password_hash
import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db, Admin, Student
from werkzeug.security import generate_password_hash
from app import create_app

app = create_app()

with app.app_context():
    # Hash passwords for all admins if not already hashed
    admins = Admin.query.all()
    for admin in admins:
        if not admin.password.startswith("pbkdf2:sha256:"):
            print(f"Hashing password for admin: {admin.email}")
            admin.password = generate_password_hash(admin.password)
    
    # Hash passwords for all students if needed
    students = Student.query.all()
    for student in students:
        if not student.password.startswith("pbkdf2:sha256:"):
            print(f"Hashing password for student: {student.email}")
            student.password = generate_password_hash(student.password)

    db.session.commit()
    print("All plain-text passwords have been hashed successfully!")
