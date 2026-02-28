import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import inspect
from core.database import engine, Base, SessionLocal
from models.core import User, Course

try:
    print("Testing DB connection and Initializing Schema...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
    
    inspector = inspect(engine)
    print(f"Tables in DB: {inspector.get_table_names()}")
    
    session = SessionLocal()
    from core.auth import hash_password
    
    if session.query(User).count() == 0:
        admin = User(
            username="admin", 
            hashed_password=hash_password("admin123"),
            email="admin@lms.local",
            full_name="System Admin",
            role="admin",
            is_active=True
        )
        student = User(
            username="student", 
            hashed_password=hash_password("student123"),
            email="student@lms.local",
            full_name="Test Student",
            role="student",
            is_active=True
        )
        teacher = User(
            username="teacher", 
            hashed_password=hash_password("teacher123"),
            email="teacher@lms.local",
            full_name="Test Teacher",
            role="teacher",
            is_active=True
        )
        session.add(admin)
        session.add(student)
        session.add(teacher)
        session.commit()
        print("Mock users seeded successfully.")
    else:
        print("Users already exist.")
        
    count = session.query(User).count()
    print(f"Current user count: {count}")
    
except Exception as e:
    import builtins
    builtins.print("Database Error Traceback:")
    traceback.print_exc(file=sys.stdout)
