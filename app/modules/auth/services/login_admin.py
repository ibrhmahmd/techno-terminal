"""Login administration functions (ADR-0005).

Provides write operations on the users table that are called by higher modules
(hr). All functions flush only; the caller commits.
"""

from app.db.uow import UnitOfWork
import app.modules.auth.repositories.auth_repository as repo
from app.shared.exceptions import NotFoundError


def set_login_active(uow: UnitOfWork, user_id: int, active: bool) -> None:
    """Set a user's active flag without touching role.

    Args:
        uow: UnitOfWork for the current use case.
        user_id: User ID to update.
        active: New is_active value.

    Raises:
        NotFoundError: If user does not exist.
    """
    auth_repo = repo.AuthRepository(uow.session)
    user = auth_repo.update_user_role_status(user_id, is_active=active)
    if user is None:
        raise NotFoundError(f"User {user_id} not found")
    uow.flush()


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