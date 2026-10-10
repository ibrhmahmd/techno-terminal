import logging
from typing import Optional
from datetime import date

from app.core.supabase_clients import get_supabase_admin, get_supabase_anon
from app.db.uow import UnitOfWork
import app.modules.auth.repositories.auth_repository as repo
from app.modules.auth.models.auth_models import User
from app.modules.auth.schemas.auth_schemas import (
    UpdateProfileInput,
    UserCreate,
    UserListResult,
    UserSessionDTO,
)
from app.modules.auth.constants import is_valid_role
from app.shared.constants import MIN_PASSWORD_LENGTH
from app.shared.exceptions import AuthError, BusinessRuleError, ConflictError, NotFoundError, ValidationError
from app.modules.auth.models.audit_log import AuditLogEventType
from app.modules.auth.services.audit_service import AuditService
from app.modules.auth.services.provisioning import provision_login, _create_supabase_user

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, uow: UnitOfWork, audit_svc: AuditService | None = None):
        self._uow = uow
        self._repo = repo.AuthRepository(uow.session)
        self._audit = audit_svc or AuditService(uow)

    def get_user_by_supabase_uid(self, uid: str) -> Optional[User]:
        """Retrieves a local user profile explicitly mapped to a verified Supabase JWT."""
        return self._repo.get_user_by_supabase_uid(uid)

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self._repo.get_user_by_username(username)

    def update_last_login(self, user_id: int) -> None:
        self._repo.update_last_login(user_id)
        self._uow.flush()

    def force_reset_password(self, user_id: int, new_password: str) -> None:
        if len(new_password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            )
        user = self._repo.get_user_by_id(user_id)
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
            logger.warning("Supabase sign-in failed during password change: %s", e)
            raise AuthError("Current password is incorrect.") from e
        admin = get_supabase_admin()
        admin.auth.admin.update_user_by_id(
            user.supabase_uid, {"password": new_password}
        )
        self._audit.log_event(
            event_type=AuditLogEventType.PASSWORD_CHANGE,
            user_id=user.id,
        )
        self._uow.commit()

    def update_profile(self, user: User, dto: UpdateProfileInput) -> User:
        if dto.username is not None:
            existing = self._repo.get_user_by_username(dto.username)
            if existing and existing.id != user.id:
                raise ConflictError(f"Username {dto.username!r} already exists.")
            user.username = dto.username
        self._repo.update_user(user)
        self._uow.commit()
        self._uow.session.refresh(user)
        return user

    def invite_user(self, email: str, role: str, employee_id: int | None) -> User:
        import uuid
        from datetime import timedelta
        from app.shared.datetime_utils import utc_now

        if not is_valid_role(role):
            raise ValidationError(f"Invalid role: {role!r}.")
        existing = self._repo.get_user_by_username(email)
        if existing:
            raise ConflictError(f"User with email {email!r} already exists.")
        if employee_id is not None:
            if not self._repo.employee_exists(employee_id):
                raise NotFoundError(f"Employee {employee_id} not found.")
        user_in = UserCreate(
            username=email,
            role=role,
            employee_id=employee_id,
            is_active=False,
            supabase_uid=None,
            invite_token=str(uuid.uuid4()),
            invite_expires_at=utc_now() + timedelta(hours=24),
        )
        user = self._repo.create_user(user_in)
        self._uow.commit()
        self._uow.session.refresh(user)
        return user

    def register_with_invite(self, token: str, username: str, password: str) -> User:
        from app.shared.datetime_utils import utc_now

        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            )
        user = self._repo.find_by_invite_token(token)
        if not user:
            raise AuthError("Invalid or expired invite token.")
        if user.invite_expires_at and user.invite_expires_at < utc_now():
            raise AuthError("Invalid or expired invite token.")
        existing = self._repo.get_user_by_username(username)
        if existing:
            raise ConflictError(f"Username {username!r} already exists.")
        native_uid = _create_supabase_user(username, password)
        user.username = username
        user.supabase_uid = native_uid
        user.is_active = True
        user.invite_token = None
        user.invite_expires_at = None
        self._repo.update_user(user)
        self._uow.commit()
        self._uow.session.refresh(user)
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
            logger.exception("Failed to log out Supabase sessions for user %s", user.id)

    def list_sessions(self, user: User) -> list[UserSessionDTO]:
        # The Supabase Python client's GoTrue Admin API does not support listing sessions.
        # Returning an empty list to avoid AttributeError and noisy logs.
        return []

    def forgot_password(self, email: str) -> None:
        try:
            supabase = get_supabase_anon()
            supabase.auth.reset_password_email(email)
        except Exception:
            logger.exception("Forgot password email failed for %s", email)

    def list_users(
        self,
        skip: int = 0,
        limit: int = 50,
        is_active: Optional[bool] = None,
        role: Optional[str] = None,
        q: Optional[str] = None,
    ) -> UserListResult:
        return self._repo.list_users(skip, limit, is_active, role, q)

    def get_user(self, user_id: int) -> User:
        user = self._repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found.")
        return user

    def update_user(self, target_user_id: int, dto, current_user: User) -> User:
        if dto.is_active is False and target_user_id == current_user.id:
            raise BusinessRuleError("Cannot deactivate your own account.")
        user = self._repo.update_user_role_status(
            target_user_id, role=dto.role, is_active=dto.is_active
        )
        if not user:
            raise NotFoundError(f"User {target_user_id} not found.")
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
        self._uow.commit()
        self._uow.session.refresh(user)
        return user

    def delete_user(self, target_user_id: int, current_user: User) -> None:
        if target_user_id == current_user.id:
            raise BusinessRuleError("Cannot delete your own account.")
        user = self._repo.get_user_by_id(target_user_id)
        if not user:
            raise NotFoundError(f"User {target_user_id} not found.")
        supabase_uid = user.supabase_uid

        if supabase_uid:
            try:
                admin = get_supabase_admin()
                admin.auth.admin.delete_user(supabase_uid)
            except Exception:
                logger.exception("Failed to delete Supabase user %s", supabase_uid)

        self._audit.log_event(
            event_type=AuditLogEventType.ACCOUNT_DELETED,
            user_id=target_user_id,
            details={"deleted_by": current_user.id},
        )
        self._repo.delete_user(target_user_id)
        self._uow.commit()

    def link_employee_to_new_user(
        self, employee_id: int | None, username: str, raw_password: str, role: str
    ) -> User:
        user = provision_login(
            self._uow,
            username=username,
            raw_password=raw_password,
            role=role,
            employee_id=employee_id,
            is_active=True,
        )
        self._uow.commit()
        self._uow.session.refresh(user)
        return user

    def evaluate_login_alert(self, user: User, ip_address: str, user_agent: str) -> str | None:
        """Evaluate whether this login triggers a security alert.

        Returns the alert reason string if an alert should be raised, else None.
        Mirrors the exact logic and message strings from the original login route.
        """
        if user.last_login is None:
            return "First time this user has ever logged in."
        if user.last_login.date() < date.today():
            return "First login of the day for this user."
        last_log = self._audit.get_last_login_event(user.id)
        if last_log:
            if last_log.ip_address and last_log.ip_address != ip_address:
                return f"Login from a new IP address (Previous: {last_log.ip_address})."
            elif last_log.user_agent and last_log.user_agent != user_agent:
                return "Login from a new device/browser."
        return None

    def record_login_failure(
        self,
        reason: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        email: str | None = None,
        supabase_uid: str | None = None,
    ) -> None:
        if reason == "invalid_credentials":
            details = {"email": email} if email else {}
        elif reason == "no_local_identity":
            details = {"supabase_uid": supabase_uid, "reason": "no local identity"}
        else:
            details = {"reason": reason}
            if email:
                details["email"] = email
        self._audit.log_event(
            event_type=AuditLogEventType.LOGIN_FAILURE,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )
        self._uow.commit()

    def record_login_success(
        self,
        user_id: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Stamp last_login, log LOGIN_SUCCESS, and commit atomically.

        This replaces the separate update_last_login + log_event calls
        in the login route to ensure the audit row is committed.
        """
        self.update_last_login(user_id)
        self._audit.log_event(
            event_type=AuditLogEventType.LOGIN_SUCCESS,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._uow.commit()