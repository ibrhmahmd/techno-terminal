import bcrypt
from app.db.connection import get_session
from app.modules.auth.auth_models import User
from app.shared.exceptions import ValidationError, AuthError, ConflictError
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


# ── Staff Management ──────────────────────────────────────────────────────────

def create_staff_account(username: str, plain_password: str, full_name: str, role: str, phone: str = None) -> dict:
    if len(plain_password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    with get_session() as session:
        existing = repo.get_user_by_username(session, username)
        if existing:
            raise ConflictError(f"Username {username} already exists.")
            
        emp_data = {
            "full_name": full_name,
            "phone": phone,
            "is_active": True,
            "job_title": role.capitalize()
        }
        user_data = {
            "username": username,
            "password_hash": hash_password(plain_password),
            "role": role,
            "is_active": True
        }
        emp, user = repo.create_employee_and_user(session, emp_data, user_data)
        session.commit()
        return {"user_id": user.id, "employee_id": emp.id, "username": user.username}


def list_staff_accounts() -> list[dict]:
    with get_session() as session:
        records = repo.get_all_users_with_employees(session)
        result = []
        for u, e in records:
            result.append({
                "user_id": u.id,
                "employee_id": e.id,
                "username": u.username,
                "full_name": e.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "phone": e.phone
            })
        return result


def update_staff_account(user_id: int, is_active: bool, role: str) -> bool:
    with get_session() as session:
        repo.update_user_and_employee(session, user_id, is_active, role)
        session.commit()
        return True


def force_reset_password(user_id: int, new_password: str) -> bool:
    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    with get_session() as session:
        repo.update_password_hash(session, user_id, hash_password(new_password))
        session.commit()
    return True
