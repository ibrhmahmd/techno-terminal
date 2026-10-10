"""User login provisioning (ADR-0005)."""

import logging
from typing import Callable, Optional

from app.core.supabase_clients import get_supabase_admin
from app.db.uow import UnitOfWork
import app.modules.auth.repositories.auth_repository as repo
from app.modules.auth.models.auth_models import User
from app.modules.auth.schemas.auth_schemas import UserCreate
from app.modules.auth.constants import is_valid_role
from app.shared.constants import MIN_PASSWORD_LENGTH
from app.shared.datetime_utils import utc_now
from app.shared.exceptions import ConflictError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


def _create_supabase_user(
    username: str, raw_password: str, *, supabase_admin=None
) -> str:
    """Create a Supabase user and return the native UID.

    Args:
        username: The username/email for the account.
        raw_password: The plaintext password.
        supabase_admin: The Supabase admin client to use; defaults to get_supabase_admin().

    Returns:
        The Supabase native user ID (native_uid).

    Raises:
        ConflictError: If Supabase user creation fails.
    """
    if supabase_admin is None:
        supabase_admin = get_supabase_admin()
    email_binding = username if "@" in username else f"{username}@system.local"
    try:
        auth_response = supabase_admin.auth.admin.create_user(
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
    supabase_admin=None,
    remote_error_mapper: Callable[[Exception], Exception] | None = None,
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
        supabase_admin: The Supabase admin client to use; defaults to get_supabase_admin().
        remote_error_mapper: Callable to map Supabase create_user exceptions; defaults to
            raising ConflictError("Supabase error: {e}").

    Returns:
        The created User (flushed, not committed).

    Raises:
        ValidationError: Password too short or invalid role.
        NotFoundError: Employee not found.
        ConflictError: Username taken, employee already linked, or Supabase error (mapped).
    """
    if supabase_admin is None:
        supabase_admin = get_supabase_admin()

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

    try:
        native_uid = _create_supabase_user(username, raw_password, supabase_admin=supabase_admin)
    except ConflictError as e:
        # _create_supabase_user wraps the original exception in ConflictError
        # Pass the original cause to the mapper if available
        original_exc = e.__cause__ or e
        if remote_error_mapper is not None:
            raise remote_error_mapper(original_exc) from e
        raise
    except Exception as e:
        if remote_error_mapper is not None:
            raise remote_error_mapper(e) from e
        raise

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
        compensate_provisioned_login(native_uid, supabase_admin=supabase_admin)
        raise


def compensate_provisioned_login(supabase_uid: str, *, supabase_admin=None) -> None:
    """Best-effort deletion of a provisioned Supabase user.

    Failure is logged and never raised. Intended for compensation after a
    local DB failure following a successful remote user creation.

    Args:
        supabase_uid: The Supabase user ID to delete.
        supabase_admin: The Supabase admin client to use; defaults to get_supabase_admin().
    """
    if supabase_admin is None:
        supabase_admin = get_supabase_admin()
    try:
        supabase_admin.auth.admin.delete_user(supabase_uid)
    except Exception:
        logger.exception(
            "orphaned auth identity %s requires manual cleanup", supabase_uid
        )