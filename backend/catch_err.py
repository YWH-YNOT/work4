import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import inspect
from core.database import engine, Base, SessionLocal
from models.core import User, Course

with open("error_log.txt", "w", encoding="utf-8") as f:
    try:
        f.write("Testing DB connection and Initializing Schema...\n")
        Base.metadata.create_all(bind=engine)
        f.write("Tables created successfully.\n")
        
        inspector = inspect(engine)
        f.write(f"Tables in DB: {inspector.get_table_names()}\n")
        
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
            session.add(admin)
            session.commit()
            f.write("Mock users seeded successfully.\n")
        else:
            f.write("Users already exist.\n")
            
        count = session.query(User).count()
        f.write(f"Current user count: {count}\n")
        
    except Exception as e:
        f.write(traceback.format_exc())
