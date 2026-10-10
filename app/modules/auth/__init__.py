# Facade of the auth module (ADR-0003). Lower modules may import from here only.
#
# Leaf exports (constants, models, schemas) are imported eagerly. The two
# services are deferred through ``__getattr__`` so that importing the facade
# never pulls in ``auth_service`` at module load time: that module still
# imports ``app.modules.hr.repositories`` (legacy ADR-0005/0006 coupling that
# Phase B relocates), which re-enters this package from HR while it is
# partially initialized and raises a circular-import error otherwise.
from app.modules.auth.constants import UserRole, ALL_ROLE_VALUES, is_valid_role
from app.modules.auth.models.auth_models import User
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
]


def __getattr__(name: str):
    if name == "AuthService":
        from app.modules.auth.services.auth_service import AuthService

        return AuthService
    if name == "AuditService":
        from app.modules.auth.services.audit_service import AuditService

        return AuditService
    raise AttributeError(name)