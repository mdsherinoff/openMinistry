"""
Create a new moderator or admin user securely.
Usage: python create_user.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

import getpass
from database.config import get_session_factory
from database.models.user import User
from api.auth import hash_password


def create_user():
    print("=== openMinistry User Creation ===\n")

    email = input("Email: ").strip()
    if not email:
        print("Email is required.")
        return

    full_name = input("Full name: ").strip()

    role = input("Role (admin/moderator) [moderator]: ").strip()
    if role not in ("admin", "moderator"):
        role = "moderator"

    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Passwords do not match.")
        return

    if len(password) < 8:
        print("Password must be at least 8 characters.")
        return

    SessionLocal = get_session_factory()
    db = SessionLocal()

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"User {email} already exists.")
        db.close()
        return

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
        is_active=1,
    )
    db.add(user)
    db.commit()
    print(f"\nCreated {role}: {email}")
    db.close()


if __name__ == "__main__":
    create_user()