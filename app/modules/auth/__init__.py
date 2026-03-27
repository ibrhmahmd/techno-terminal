"""
app/modules/auth/__init__.py — Compatibility Facade
────────────────────────────────────────────────────
Instantiates AuthService and re-exports all operations and types at the
top level so existing imports continue to work without change.
"""
from app.modules.auth.services.auth_service import AuthService
from app.modules.auth.models.auth_models import User, UserBase
from app.modules.auth.schemas.auth_schemas import UserCreate, UserPublic, UserRead
from app.modules.auth.constants import UserRole, ALL_ROLE_VALUES, is_valid_role

# ── Singleton service instance ────────────────────────────────────────────────
_auth_service = AuthService()

# ── Direct function aliases (backward compatibility) ─────────────────────────
get_user_by_supabase_uid  = _auth_service.get_user_by_supabase_uid
get_user_by_username      = _auth_service.get_user_by_username
get_users_for_employee    = _auth_service.get_users_for_employee
link_employee_to_new_user = _auth_service.link_employee_to_new_user
update_last_login         = _auth_service.update_last_login
force_reset_password      = _auth_service.force_reset_password

__all__ = [
    # Service
    "_auth_service",
    # Models
    "User",
    "UserBase",
    "UserCreate",
    "UserPublic",
    "UserRead",
    # Constants
    "UserRole",
    "ALL_ROLE_VALUES",
    "is_valid_role",
    # Function aliases
    "get_user_by_supabase_uid",
    "get_user_by_username",
    "get_users_for_employee",
    "link_employee_to_new_user",
    "update_last_login",
    "force_reset_password",
]
