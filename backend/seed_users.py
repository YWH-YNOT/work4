import sys, os, traceback
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from models.core import User
from core.auth import hash_password

session = SessionLocal()
try:
    usernames = [u.username for u in session.query(User).all()]
    print(f"Existing users: {usernames}")

    if "student" not in usernames:
        session.add(User(
            username="student",
            hashed_password=hash_password("student123"),
            email="student@lms.local",
            full_name="Test Student",
            role="student",
            is_active=True
        ))
        print("Inserted student")

    if "teacher" not in usernames:
        session.add(User(
            username="teacher",
            hashed_password=hash_password("teacher123"),
            email="teacher@lms.local",
            full_name="Test Teacher",
            role="teacher",
            is_active=True
        ))
        print("Inserted teacher")

    session.commit()
    print("Done. Total users:", session.query(User).count())
except Exception:
    traceback.print_exc()
