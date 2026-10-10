from typing import Optional
from sqlmodel import Session, select, func

from app.shared.datetime_utils import utc_now
from app.modules.auth.models.auth_models import User
from app.modules.auth.schemas.auth_schemas import UserCreate, UserListResult


class AuthRepository:
    """Repository for auth data access."""

    def __init__(self, session: Session):
        self._session = session

    def get_user_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return self._session.exec(stmt).first()

    def get_user_by_supabase_uid(self, uid: str) -> User | None:
        stmt = select(User).where(User.supabase_uid == uid)
        return self._session.exec(stmt).first()

    def get_users_by_employee_id(self, employee_id: int) -> list[User]:
        stmt = select(User).where(User.employee_id == employee_id)
        return list(self._session.exec(stmt).all())

    def create_user(self, data: UserCreate) -> User:
        user = User(**data.model_dump())
        user.created_at = utc_now()
        self._session.add(user)
        self._session.flush()
        return user

    def update_last_login(self, user_id: int) -> None:
        user = self._session.get(User, user_id)
        if user:
            user.last_login = utc_now()
            self._session.add(user)

    def get_user_by_id(self, user_id: int) -> User | None:
        return self._session.get(User, user_id)

    def update_user(self, user: User) -> User:
        self._session.add(user)
        self._session.flush()
        return user

    def list_users(
        self,
        skip: int = 0,
        limit: int = 50,
        is_active: Optional[bool] = None,
        role: Optional[str] = None,
        q: Optional[str] = None,
    ) -> UserListResult:
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

        total = self._session.exec(count_query).one()
        results = list(self._session.exec(query).all())
        return UserListResult(items=results, total=total)

    def update_user_role_status(
        self, user_id: int, role: Optional[str] = None, is_active: Optional[bool] = None
    ) -> Optional[User]:
        user = self._session.get(User, user_id)
        if not user:
            return None
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        self._session.add(user)
        self._session.flush()
        return user

    def delete_user(self, user_id: int) -> Optional[User]:
        user = self._session.get(User, user_id)
        if not user:
            return None
        self._session.delete(user)
        self._session.flush()
        return user

    def find_by_invite_token(self, token: str) -> Optional[User]:
        stmt = select(User).where(User.invite_token == token)
        return self._session.exec(stmt).first()

    def employee_exists(self, employee_id: int) -> bool:
        # Local import to avoid circular dependency: hr's __init__ imports auth facade
        from app.modules.hr.models import Employee
        return self._session.get(Employee, employee_id) is not None