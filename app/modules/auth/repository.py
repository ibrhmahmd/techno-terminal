from datetime import datetime, timezone
from sqlmodel import Session, select
from .models import User, Employee


def get_user_by_username(session: Session, username: str) -> User | None:
    stmt = select(User).where(User.username == username)
    return session.exec(stmt).first()


def get_employee_by_id(session: Session, employee_id: int) -> Employee | None:
    return session.get(Employee, employee_id)


def update_password_hash(session: Session, user_id: int, new_hash: str) -> None:
    user = session.get(User, user_id)
    if user:
        user.password_hash = new_hash
        user.updated_at = datetime.now(timezone.utc)
        session.add(user)


def update_last_login(session: Session, user_id: int) -> None:
    user = session.get(User, user_id)
    if user:
        user.last_login = datetime.now(timezone.utc)
        session.add(user)
