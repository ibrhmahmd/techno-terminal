from typing import Optional

from app.core.supabase_clients import get_supabase_admin, get_supabase_anon
from app.db.connection import get_session
import app.modules.auth.repositories.auth_repository as repo
from app.modules.auth.models.auth_models import User
from app.modules.auth.schemas.auth_schemas import UpdateProfileInput, UserCreate
from app.modules.auth.constants import is_valid_role
from app.modules.hr.repositories import EmployeeRepository
from app.shared.constants import MIN_PASSWORD_LENGTH
from app.shared.exceptions import AuthError, BusinessRuleError, ConflictError, NotFoundError, ValidationError

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

    def force_reset_password(self, user_id: int, new_password: str) -> None:
        if len(new_password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            )
        with get_session() as session:
            user = repo.get_user_by_id(session, user_id)
            if not user:
                raise NotFoundError(f"User {user_id} not found.")
            if not user.is_active:
                raise BusinessRuleError(
                    f"Cannot reset password for deactivated user {user_id}."
                )
            supabase_uid = user.supabase_uid

        admin = get_supabase_admin()
        admin.auth.admin.update_user_by_id(
            supabase_uid, {"password": new_password}
        )

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if len(new_password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            )
        email_binding = user.username if "@" in user.username else f"{user.username}@system.local"
        supabase = get_supabase_anon()
        try:
            supabase.auth.sign_in_with_password(
                {"email": email_binding, "password": current_password}
            )
        except Exception as e:
            raise AuthError("Current password is incorrect.") from e
        admin = get_supabase_admin()
        admin.auth.admin.update_user_by_id(
            user.supabase_uid, {"password": new_password}
        )

    def update_profile(self, user: User, dto: UpdateProfileInput) -> User:
        with get_session() as session:
            if dto.username is not None:
                existing = repo.get_user_by_username(session, dto.username)
                if existing and existing.id != user.id:
                    raise ConflictError(f"Username {dto.username!r} already exists.")
                user.username = dto.username
            repo.update_user(session, user)
            session.commit()
            session.refresh(user)
            return user

    def forgot_password(self, email: str) -> None:
        try:
            supabase = get_supabase_anon()
            supabase.auth.reset_password_email(email)
        except Exception:
            pass

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
            emp_repo = EmployeeRepository(session)
            emp = emp_repo.get_by_id(employee_id)
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
            try:
                user = repo.create_user(session, user_in)
                session.commit()
                session.refresh(user)
                return user
            except Exception:
                session.rollback()
                try:
                    admin.auth.admin.delete_user(native_uid)
                except Exception:
                    pass
                raise
