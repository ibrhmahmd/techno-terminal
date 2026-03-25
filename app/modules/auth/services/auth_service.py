from typing import List, Optional

from app.core.supabase_clients import get_supabase_admin
from app.db.connection import get_session
from app.modules.auth.repositories import auth_repository as repo
from app.modules.auth.models.auth_models import User
from app.modules.auth.schemas.auth_schemas import UserCreate
from app.modules.auth.constants import is_valid_role
from app.modules.hr import hr_repository as hr_repo
from app.shared.constants import MIN_PASSWORD_LENGTH
from app.shared.exceptions import ConflictError, NotFoundError, ValidationError

class AuthService:
    def get_user_by_supabase_uid(self, uid: str) -> Optional[User]:
        """Retrieves a local user profile explicitly mapped to a verified Supabase JWT."""
        with get_session() as session:
            return repo.get_user_by_supabase_uid(session, uid)

    def get_user_by_username(self, username: str) -> Optional[User]:
        with get_session() as session:
            return repo.get_user_by_username(session, username)

    def update_last_login(self, user_id: int) -> None:
        with get_session() as session:
            repo.update_last_login(session, user_id)
            session.commit()

    def get_users_for_employee(self, employee_id: int) -> List[User]:
        with get_session() as session:
            return repo.get_users_by_employee_id(session, employee_id)

    def force_reset_password(self, user_id: int, new_password: str) -> None:
        if len(new_password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            )
        with get_session() as session:
            user = repo.get_user_by_id(session, user_id)
            if not user:
                raise NotFoundError(f"User {user_id} not found.")
            # Read identity while session is open; detached User may lazy-load after close.
            supabase_uid = user.supabase_uid

        admin = get_supabase_admin()
        admin.auth.admin.update_user_by_id(
            supabase_uid, {"password": new_password}
        )

    def link_employee_to_new_user(
        self, employee_id: int, username: str, raw_password: str, role: str
    ) -> User:
        if len(raw_password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            )
        if not is_valid_role(role):
            raise ValidationError(f"Invalid role: {role!r}.")

        with get_session() as session:
            emp = hr_repo.get_employee_by_id(session, employee_id)
            if not emp:
                raise NotFoundError(f"Employee {employee_id} not found.")
            if repo.get_users_by_employee_id(session, employee_id):
                raise ConflictError("This employee already has a linked login.")
            if repo.get_user_by_username(session, username):
                raise ConflictError(f"Username {username!r} already exists.")

            email_binding = username if "@" in username else f"{username}@system.local"
            admin = get_supabase_admin()
            try:
                auth_response = admin.auth.admin.create_user(
                    {
                        "email": email_binding,
                        "password": raw_password,
                        "email_confirm": True,
                    }
                )
                native_uid = auth_response.user.id
            except Exception as e:
                raise ConflictError(f"Supabase error: {e}") from e

            user_in = UserCreate(
                username=username,
                role=role,
                employee_id=employee_id,
                is_active=True,
                supabase_uid=native_uid,
            )
            user = repo.create_user(session, user_in.model_dump())
            session.commit()
            session.refresh(user)
            return user
