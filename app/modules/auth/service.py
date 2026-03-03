import bcrypt
from app.db.connection import get_session
from app.modules.auth.models import User
from . import repository as repo

MIN_PASSWORD_LENGTH = 6


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def authenticate(username: str, password: str):
    with get_session() as session:
        user = repo.get_user_by_username(session, username)
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        repo.update_last_login(session, user.id)
        return user


def change_password(user_id: int, current_password: str, new_password: str) -> bool:
    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect.")
        new_hash = hash_password(new_password)
        repo.update_password_hash(session, user_id, new_hash)
    return True


def get_active_instructors() -> list[User]:  # Just returning Employees
    with get_session() as session:
        return list(repo.get_active_employees(session))
