import bcrypt
from app.db.connection import get_session
from app.modules.auth.auth_models import User
from app.shared.exceptions import ValidationError, AuthError
from . import auth_repository as repo

MIN_PASSWORD_LENGTH = 12

# Module-level constant: used as a fallback hash to ensure verify_password()
# is always called — even for unknown usernames — preventing timing-based
# username enumeration.
_DUMMY_HASH: str = ""  # populated lazily on first authenticate() call


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def authenticate(username: str, password: str):
    """
    Authenticates a user. Always calls verify_password() regardless of whether the
    username exists — this ensures constant response time and prevents timing-based
    username enumeration attacks.
    """
    global _DUMMY_HASH
    if not _DUMMY_HASH:
        # Lazily initialize once — avoids paying bcrypt cost at import time
        _DUMMY_HASH = hash_password("_dummy_unused_protect_timing_")

    with get_session() as session:
        user = repo.get_user_by_username(session, username)

    # Always hash — constant-time path for valid and invalid usernames alike
    candidate_hash = user.password_hash if user else _DUMMY_HASH
    if not verify_password(password, candidate_hash):
        return None
    if not user or not user.is_active:
        return None

    # Update last login in a separate session (no read+write lock conflict)
    with get_session() as session:
        repo.update_last_login(session, user.id)

    return user


def change_password(user_id: int, current_password: str, new_password: str) -> bool:
    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            raise AuthError("User not found.")
        if not verify_password(current_password, user.password_hash):
            raise AuthError("Current password is incorrect.")
        new_hash = hash_password(new_password)
        repo.update_password_hash(session, user_id, new_hash)
    return True


def get_active_instructors() -> list[User]:  # Just returning Employees
    with get_session() as session:
        return list(repo.get_active_employees(session))
