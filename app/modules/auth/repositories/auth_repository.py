from typing import Optional
from sqlmodel import Session, select, func
from app.shared.datetime_utils import utc_now
from app.modules.auth.models.auth_models import User
from app.modules.auth.schemas.auth_schemas import UserCreate
from app.modules.hr.models import Employee

def get_user_by_username(session: Session, username: str) -> User | None:
    stmt = select(User).where(User.username == username)
    return session.exec(stmt).first()

def get_user_by_supabase_uid(session: Session, uid: str) -> User | None:
    stmt = select(User).where(User.supabase_uid == uid)
    return session.exec(stmt).first()

def get_users_by_employee_id(session: Session, employee_id: int) -> list[User]:
    stmt = select(User).where(User.employee_id == employee_id)
    return list(session.exec(stmt).all())

def create_user(session: Session, data: UserCreate) -> User:
    user = User(**data.model_dump())
    session.add(user)
    session.flush()
    return user

def update_last_login(session: Session, user_id: int) -> None:
    user = session.get(User, user_id)
    if user:
        user.last_login = utc_now()
        session.add(user)

# ── RepositoryProtocol aliases ────────────────────────────────────────────────
def get_user_by_id(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)


def update_user(session: Session, user: User) -> User:
    session.add(user)
    session.flush()
    return user


def list_users(
    session: Session,
    skip: int = 0,
    limit: int = 50,
    is_active: Optional[bool] = None,
    role: Optional[str] = None,
    q: Optional[str] = None,
) -> tuple[list[User], int]:
    query = select(User)
    count_query = select(func.count(User.id))

    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)
    if role is not None:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)
    if q is not None:
        pattern = f"%{q}%"
        query = query.where(User.username.ilike(pattern))
        count_query = count_query.where(User.username.ilike(pattern))

    query = query.order_by(User.id).offset(skip).limit(limit)

    total = session.exec(count_query).one()
    results = list(session.exec(query).all())
    return results, total


def update_user_role_status(
    session: Session, user_id: int, role: Optional[str] = None, is_active: Optional[bool] = None
) -> Optional[User]:
    user = session.get(User, user_id)
    if not user:
        return None
    if role is not None:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    session.add(user)
    session.flush()
    return user


def deactivate_user(session: Session, user_id: int) -> Optional[User]:
    user = session.get(User, user_id)
    if not user:
        return None
    user.is_active = False
    user.supabase_uid = ""
    session.add(user)
    session.flush()
    return user


def find_by_invite_token(session: Session, token: str) -> Optional[User]:
    stmt = select(User).where(User.invite_token == token)
    return session.exec(stmt).first()