"""
Run this once to create the first admin user.
Usage: python seed.py
Or with custom credentials:
ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=securepass python seed.py
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

    # Read from environment or prompt
    admin_email = os.environ.get("ADMIN_EMAIL", "administrator@openministry.live")
    admin_password = os.environ.get("ADMIN_PASSWORD")

    if not admin_password:
        import getpass
        print("No ADMIN_PASSWORD env var found.")
        admin_password = getpass.getpass("Enter admin password: ")

    existing = db.query(User).filter(
        User.email == admin_email
    ).first()

    if existing:
        print(f"User {admin_email} already exists.")
        db.close()
        return

    admin = User(
        email=admin_email,
        hashed_password=hash_password(admin_password),
        full_name="Admin User",
        role="admin",
        is_active=1,
    )
    db.add(admin)
    db.commit()
    print(f"Created admin: {admin_email}")
    db.close()


if __name__ == "__main__":
    seed()