import hashlib
import secrets
from sqlalchemy.orm import Session
from models import Admin

# Simple session store
sessions = {}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def create_session(admin_id: int) -> str:
    token = secrets.token_hex(32)
    sessions[token] = admin_id
    return token


def get_admin_from_session(token: str, db: Session):
    admin_id = sessions.get(token)
    if admin_id is None:
        return None
    return db.query(Admin).filter(Admin.id == admin_id).first()


def delete_session(token: str):
    sessions.pop(token, None)


def create_default_admin(db: Session):
    existing = db.query(Admin).filter(Admin.username == "admin").first()
    if not existing:
        admin = Admin(
            username="admin",
            password_hash=hash_password("admin123")
        )
        db.add(admin)
        db.commit()
        print("✅ Default admin created: admin / admin123")
    else:
        print("✅ Admin account already exists")
