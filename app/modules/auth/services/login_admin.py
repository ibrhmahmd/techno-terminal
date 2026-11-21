"""Login administration functions (ADR-0005).

Provides write operations on the users table that are called by higher modules
(hr). All functions flush only; the caller commits.
"""

import logging

from app.core.supabase_clients import get_supabase_admin
from app.db.uow import UnitOfWork
import app.modules.auth.repositories.auth_repository as repo
from app.shared.exceptions import NotFoundError

logger = logging.getLogger(__name__)

# Supabase has no permanent ban; ~100 years (#274).
BAN_DURATION = "876000h"


def sync_supabase_ban(supabase_uids: list[str | None], banned: bool) -> None:
    """Ban or unban the Supabase users of deactivated or reactivated logins (#274).

    Call AFTER the local commit (ADR-0001). Best-effort: a failure is logged and
    never fails the local change (#250 still refuses tokens to inactive users).
    """
    for uid in filter(None, supabase_uids):
        try:
            get_supabase_admin().auth.admin.update_user_by_id(
                uid, {"ban_duration": BAN_DURATION if banned else "none"}
            )
        except Exception:
            logger.exception("Failed to %s Supabase user %s", "ban" if banned else "unban", uid)


def set_login_active(uow: UnitOfWork, user_id: int, active: bool) -> str | None:
    """Set a user's active flag without touching role.

    Args:
        uow: UnitOfWork for the current use case.
        user_id: User ID to update.
        active: New is_active value.

    Raises:
        NotFoundError: If user does not exist.

    Returns:
        The user's Supabase uid, for sync_supabase_ban after the commit.
    """
    auth_repo = repo.AuthRepository(uow.session)
    user = auth_repo.update_user_role_status(user_id, is_active=active)
    if user is None:
        raise NotFoundError(f"User {user_id} not found")
    uow.flush()
    return user.supabase_uid


def update_login_status(uow: UnitOfWork, user_id: int, is_active: bool, role: str) -> None:
    """Update a user's active status and role.

    Args:
        uow: UnitOfWork for the current use case.
        user_id: User ID to update.
        is_active: New active status.
        role: New role string.

    Raises:
        NotFoundError: If user does not exist.
    """
    auth_repo = repo.AuthRepository(uow.session)
    user = auth_repo.update_user_role_status(user_id, role=role, is_active=is_active)
    if user is None:
        raise NotFoundError(f"User {user_id} not found")
    uow.flush()