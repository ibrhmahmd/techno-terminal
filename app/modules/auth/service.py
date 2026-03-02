from passlib.context import CryptContext
from app.db.connection import get_session
from .models import User
from . import repository as repo

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MIN_PASSWORD_LENGTH = 6


def authenticate(username: str, password: str):
    with get_session() as session:
        user = repo.get_user_by_username(session, username)
        if not user or not user.is_active:
            return None
        if not _pwd_context.verify(password, user.password_hash):
            return None
        repo.update_last_login(session, user.id)
        return user


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def change_password(user_id: int, current_password: str, new_password: str) -> bool:
    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")
        if not _pwd_context.verify(current_password, user.password_hash):
            raise ValueError("Current password is incorrect.")
        new_hash = _pwd_context.hash(new_password)
        repo.update_password_hash(session, user_id, new_hash)
    return True
