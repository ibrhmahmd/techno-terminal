# Facade of the auth module (ADR-0003). Lower modules may import from here only.

from app.modules.auth.constants import UserRole, ALL_ROLE_VALUES, is_valid_role
from app.modules.auth.models.auth_models import User
from app.modules.auth.ports import AuthNotifier
from app.modules.auth.schemas.auth_schemas import (
    AuditLogEntryDTO,
    AuditLogQueryResult,
    InviteResultDTO,
    UpdateProfileInput,
    UserAdminDTO,
    UserListResult,
    UserPublic,
    UserSessionDTO,
)
from app.modules.auth.services.auth_service import AuthService
from app.modules.auth.services.audit_service import AuditService
from app.modules.auth.services.lookup import lookup_user_by_supabase_uid
from app.modules.auth.services.provisioning import provision_login

__all__ = [
    "AuthService",
    "AuditService",
    "User",
    "UserRole",
    "AuditLogEntryDTO",
    "AuditLogQueryResult",
    "InviteResultDTO",
    "UserAdminDTO",
    "UserPublic",
    "UserSessionDTO",
    "UserListResult",
    "UpdateProfileInput",
    "ALL_ROLE_VALUES",
    "is_valid_role",
    "lookup_user_by_supabase_uid",
    "provision_login",
    "AuthNotifier",
]