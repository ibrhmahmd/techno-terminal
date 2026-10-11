"""
app/api/deps.py
───────────────
Shared FastAPI dependencies (ADR-0002): everything module-specific lives in
``app/modules/<module>/api/deps.py``.

  1. ``get_uow`` / ``UoW``: the per-request Unit of Work (ADR-0001).
  2. ``get_current_user``: validates the Supabase JWT and loads the local user.
  3. Role guards: ``require_admin``, ``require_system_admin``, ``require_any``.
"""
import logging
from typing import Annotated, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db.uow import UnitOfWork, unit_of_work
from app.core.supabase_clients import get_supabase_anon, get_supabase_admin
from app.modules.auth import User
from app.modules.auth.constants import UserRole

logger = logging.getLogger(__name__)

# ── Infrastructure ─────────────────────────────────────────────────────────────

http_bearer = HTTPBearer(auto_error=True)


def get_uow() -> Generator[UnitOfWork, None, None]:
    """Per-request UnitOfWork. Uncommitted work is rolled back on exit; never commits."""
    with unit_of_work() as uow:
        yield uow


# scope="function" ends the dependency before the response is sent, so a
# failed commit surfaces as an error response instead of a 200 already sent.
UoW = Annotated[UnitOfWork, Depends(get_uow, scope="function")]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> User:
    """
    Validates the Bearer JWT with Supabase and returns the mapped local User.
    Raises 401 for missing/invalid tokens, 403 for inactive accounts.
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials with Supabase",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        supabase = get_supabase_anon()
        auth_response = supabase.auth.get_user(token)
        if not auth_response or not auth_response.user:
            raise credentials_exception
        supabase_uid = auth_response.user.id

    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Supabase JWT validation failed: %s", type(e).__name__)
        raise credentials_exception

    from app.modules.auth import lookup_user_by_supabase_uid

    user = lookup_user_by_supabase_uid(supabase_uid)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


# ── Role Guards ────────────────────────────────────────────────────────────────

def _require_roles(*roles: UserRole):
    """
    Factory that returns a FastAPI dependency enforcing one of the given roles.

    Usage:
        @router.post("/something")
        def do_thing(_user: User = Depends(require_admin)):
            ...
    """
    role_values = {r.value for r in roles}

    async def _guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {sorted(role_values)}",
            )
        return user

    return _guard


# Convenience shortcuts — use these directly in router Depends() calls.
require_admin = _require_roles(
    UserRole.ADMIN,
    UserRole.SYSTEM_ADMIN,
)
require_system_admin = _require_roles(UserRole.SYSTEM_ADMIN)
# Any valid, active, authenticated user.
require_any = get_current_user
