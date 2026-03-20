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

# ── Pure Employee Endpoints ──────────────────────────────────────────────────

def list_all_employees() -> list[dict]:
    with get_session() as session:
        return list(repo.get_all_employees(session))

def get_employee_by_id(emp_id: int):
    with get_session() as session:
        from app.shared.exceptions import NotFoundError
        emp = repo.get_employee_by_id(session, emp_id)
        if not emp: raise NotFoundError(f"Employee {emp_id} not found.")
        return emp

def create_employee_only(data: dict):
    with get_session() as session:
        emp = repo.create_employee(session, data)
        session.commit()
        session.refresh(emp)
        return emp

def update_employee_only(emp_id: int, data: dict):
    from app.shared.exceptions import NotFoundError
    with get_session() as session:
        emp = repo.update_employee(session, emp_id, data)
        if not emp: raise NotFoundError(f"Employee {emp_id} not found.")
        session.commit()
        session.refresh(emp)
        return emp

def get_users_for_employee(emp_id: int) -> list[dict]:
    with get_session() as session:
        from sqlmodel import select
        from app.modules.auth.auth_models import User
        stmt = select(User).where(User.employee_id == emp_id)
        return session.exec(stmt).all()
        
def link_employee_to_new_user(emp_id: int, username: str, plain_password: str, role: str):
    if len(plain_password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be >= {MIN_PASSWORD_LENGTH} chars.")
    with get_session() as session:
        existing = repo.get_user_by_username(session, username)
        if existing: raise ConflictError("Username taken.")
        from app.modules.auth.auth_models import User
        user = User(username=username, password_hash=hash_password(plain_password), role=role, employee_id=emp_id)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
