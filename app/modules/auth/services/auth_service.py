from typing import Optional

from app.core.supabase_clients import get_supabase_admin, get_supabase_anon
from app.db.connection import get_session
import app.modules.auth.repositories.auth_repository as repo
from app.modules.auth.models.auth_models import User
from app.modules.auth.schemas.auth_schemas import (
    UpdateProfileInput,
    UserCreate,
    UserListResult,
    UserSessionDTO,
)
from app.modules.auth.constants import is_valid_role
from app.modules.hr.repositories import EmployeeRepository
from app.shared.constants import MIN_PASSWORD_LENGTH
from app.shared.exceptions import AuthError, BusinessRuleError, ConflictError, NotFoundError, ValidationError
from app.modules.auth.models.audit_log import AuditLogEventType
from app.modules.auth.services.audit_service import AuditService


class AuthService:
    def __init__(self, audit_svc: AuditService | None = None):
        self._audit = audit_svc or AuditService()

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
        self._audit.log_event(
            event_type=AuditLogEventType.PASSWORD_CHANGE,
            user_id=user.id,
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

    def invite_user(self, email: str, role: str, employee_id: int) -> User:
        import uuid
        from datetime import timedelta
        from app.shared.datetime_utils import utc_now

        if not is_valid_role(role):
            raise ValidationError(f"Invalid role: {role!r}.")
        with get_session() as session:
            existing = repo.get_user_by_username(session, email)
            if existing:
                raise ConflictError(f"User with email {email!r} already exists.")
            user_in = UserCreate(
                username=email,
                role=role,
                employee_id=employee_id,
                is_active=False,
                supabase_uid="",
                invite_token=str(uuid.uuid4()),
                invite_expires_at=utc_now() + timedelta(hours=24),
            )
            user = repo.create_user(session, user_in)
            session.commit()
            session.refresh(user)
            return user

    def register_with_invite(self, token: str, username: str, password: str) -> User:
        from app.shared.datetime_utils import utc_now

        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            )
        with get_session() as session:
            user = repo.find_by_invite_token(session, token)
            if not user:
                raise AuthError("Invalid or expired invite token.")
            if user.invite_expires_at and user.invite_expires_at < utc_now():
                raise AuthError("Invalid or expired invite token.")
            existing = repo.get_user_by_username(session, username)
            if existing:
                raise ConflictError(f"Username {username!r} already exists.")
            email_binding = username if "@" in username else f"{username}@system.local"
            admin = get_supabase_admin()
            try:
                auth_response = admin.auth.admin.create_user(
                    {
                        "email": email_binding,
                        "password": password,
                        "email_confirm": True,
                    }
                )
                native_uid = auth_response.user.id
            except Exception as e:
                raise ConflictError(f"Supabase error: {e}") from e
            user.username = username
            user.supabase_uid = native_uid
            user.is_active = True
            user.invite_token = None
            user.invite_expires_at = None
            repo.update_user(session, user)
            session.commit()
            session.refresh(user)
            return user

    def change_email(self, user: User, new_email: str) -> None:
        admin = get_supabase_admin()
        try:
            admin.auth.admin.update_user_by_id(
                user.supabase_uid, {"email": new_email}
            )
        except Exception as e:
            raise ConflictError(f"Email already in use: {e}") from e

    def logout_all_sessions(self, user: User) -> None:
        try:
            admin = get_supabase_admin()
            admin.auth.admin.sign_out(user.supabase_uid)
        except Exception:
            pass

    def list_sessions(self, user: User) -> list[UserSessionDTO]:
        admin = get_supabase_admin()
        try:
            sessions = admin.auth.admin.list_sessions(user.supabase_uid)
            results = []
            for s in sessions:
                results.append(UserSessionDTO(
                    id=getattr(s, "id", ""),
                    created_at=getattr(s, "created_at", None),
                    last_active_at=getattr(s, "last_active_at", None),
                    ip=getattr(s, "ip", None),
                    user_agent=getattr(s, "user_agent", None),
                ))
            return results
        except Exception:
            return []

    def forgot_password(self, email: str) -> None:
        try:
            supabase = get_supabase_anon()
            supabase.auth.reset_password_email(email)
        except Exception:
            pass

    def list_users(
        self,
        skip: int = 0,
        limit: int = 50,
        is_active: Optional[bool] = None,
        role: Optional[str] = None,
        q: Optional[str] = None,
    ) -> UserListResult:
        with get_session() as session:
            items, total = repo.list_users(session, skip, limit, is_active, role, q)
            return UserListResult(items=items, total=total)

    def get_user(self, user_id: int) -> User:
        with get_session() as session:
            user = repo.get_user_by_id(session, user_id)
            if not user:
                raise NotFoundError(f"User {user_id} not found.")
            return user

    def update_user(self, target_user_id: int, dto, current_user: User) -> User:
        if dto.is_active is False and target_user_id == current_user.id:
            raise BusinessRuleError("Cannot deactivate your own account.")
        with get_session() as session:
            user = repo.update_user_role_status(
                session, target_user_id, role=dto.role, is_active=dto.is_active
            )
            if not user:
                raise NotFoundError(f"User {target_user_id} not found.")
            session.commit()
            session.refresh(user)
            details = {}
            if dto.role:
                details["new_role"] = dto.role
            if dto.is_active is not None:
                details["new_is_active"] = dto.is_active
            if details:
                self._audit.log_event(
                    event_type=AuditLogEventType.ROLE_CHANGED,
                    user_id=target_user_id,
                    details={"changed_by": current_user.id, **details},
                )
            return user

    def deactivate_user(self, target_user_id: int, current_user: User) -> None:
        if target_user_id == current_user.id:
            raise BusinessRuleError("Cannot deactivate your own account.")
        with get_session() as session:
            user = repo.get_user_by_id(session, target_user_id)
            if not user:
                raise NotFoundError(f"User {target_user_id} not found.")
            supabase_uid = user.supabase_uid

        if supabase_uid:
            try:
                admin = get_supabase_admin()
                admin.auth.admin.delete_user(supabase_uid)
            except Exception:
                pass

        with get_session() as session:
            repo.deactivate_user(session, target_user_id)
            session.commit()
        self._audit.log_event(
            event_type=AuditLogEventType.ACCOUNT_DEACTIVATED,
            user_id=target_user_id,
            details={"deactivated_by": current_user.id},
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
