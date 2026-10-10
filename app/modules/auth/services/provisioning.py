"""User login provisioning (ADR-0005)."""

import logging
from typing import Optional

from app.core.supabase_clients import get_supabase_admin
from app.db.uow import UnitOfWork
import app.modules.auth.repositories.auth_repository as repo
from app.modules.auth.models.auth_models import User
from app.modules.auth.schemas.auth_schemas import UserCreate
from app.modules.auth.constants import is_valid_role
from app.shared.constants import MIN_PASSWORD_LENGTH
from app.shared.exceptions import ConflictError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


def _create_supabase_user(username: str, raw_password: str) -> str:
    """Create a Supabase user and return the native UID.

    Args:
        username: The username/email for the account.
        raw_password: The plaintext password.

    Returns:
        The Supabase native user ID (native_uid).

    Raises:
        ConflictError: If Supabase user creation fails.
    """
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
        return auth_response.user.id
    except Exception as e:
        raise ConflictError(f"Supabase error: {e}") from e


def provision_login(
    uow: UnitOfWork,
    *,
    username: str,
    raw_password: str,
    role: str,
    employee_id: Optional[int] = None,
    is_active: bool = True,
) -> User:
    """Provision a new login: create Supabase user, insert local users row (flush only).

    Caller commits. On DB insert/flush failure, the Supabase user is deleted
    (best-effort cleanup; failure logged) and the original exception re-raised.

    Args:
        uow: UnitOfWork for the current use case.
        username: Username (email or plain name).
        raw_password: Plaintext password (validated for length).
        role: User role string.
        employee_id: Optional employee ID to link.
        is_active: Whether the user is active (default True).

    Returns:
        The created User (flushed, not committed).

    Raises:
        ValidationError: Password too short or invalid role.
        NotFoundError: Employee not found.
        ConflictError: Username taken, employee already linked, or Supabase error.
    """
    if len(raw_password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
        )
    if not is_valid_role(role):
        raise ValidationError(f"Invalid role: {role!r}.")

    auth_repo = repo.AuthRepository(uow.session)

    if employee_id is not None:
        if not auth_repo.employee_exists(employee_id):
            raise NotFoundError(f"Employee {employee_id} not found.")
        if auth_repo.get_users_by_employee_id(employee_id):
            raise ConflictError("This employee already has a linked login.")

    if auth_repo.get_user_by_username(username):
        raise ConflictError(f"Username {username!r} already exists.")

    native_uid = _create_supabase_user(username, raw_password)

    user_in = UserCreate(
        username=username,
        role=role,
        employee_id=employee_id,
        is_active=is_active,
        supabase_uid=native_uid,
    )
    try:
        user = auth_repo.create_user(user_in)
        uow.flush()
        return user
    except Exception:
        uow.rollback()
        try:
            admin = get_supabase_admin()
            admin.auth.admin.delete_user(native_uid)
        except Exception:
            logger.exception(
                "Failed to clean up Supabase user %s after DB rollback", native_uid
            )
        raise