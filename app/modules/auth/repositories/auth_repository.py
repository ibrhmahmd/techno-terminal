from sqlmodel import Session, select
from app.shared.datetime_utils import utc_now
from app.modules.auth.models.auth_models import User
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

def create_user(session: Session, user_data: dict) -> User:
    user = User(**user_data)
    session.add(user)
    session.flush()
    return user

def update_last_login(session: Session, user_id: int) -> None:
    user = session.get(User, user_id)
    if user:
        user.last_login = utc_now()
        session.add(user)

def update_user(session: Session, user_id: int, user_data: dict) -> User | None:
    user = session.get(User, user_id)
    if not user:
        return None
    for k, v in user_data.items():
        if hasattr(user, k) and k != 'id':
            setattr(user, k, v)
    session.add(user)
    return user

# ── RepositoryProtocol aliases ────────────────────────────────────────────────
def get_user_by_id(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)
