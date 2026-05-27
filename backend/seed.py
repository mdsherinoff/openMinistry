"""
Run this once to create the first admin user.
Usage: python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from database.config import get_session_factory
from database.models.user import User
from api.auth import hash_password


def seed():
    SessionLocal = get_session_factory()
    db = SessionLocal()

    # Check if admin already exists
    existing = db.query(User).filter(User.email == "admin@openministry.in").first()
    if existing:
        print("Admin user already exists.")
        db.close()
        return

    admin = User(
        email="admin@openministry.in",
        hashed_password=hash_password("admin123"),
        full_name="Admin User",
        role="admin",
        is_active=1,
    )
    db.add(admin)

    moderator = User(
        email="moderator@openministry.in",
        hashed_password=hash_password("mod123"),
        full_name="Moderator User",
        role="moderator",
        is_active=1,
    )
    db.add(moderator)
    db.commit()
    print("Created admin: admin@openministry.in / admin123")
    print("Created moderator: moderator@openministry.in / mod123")
    db.close()


if __name__ == "__main__":
    seed()