"""Auth HTTP-layer service factories (ADR-0002: api/ → services/)."""

from app.api.dependencies import UoW
from app.modules.auth import AuthService, AuditService


def get_auth_service(uow: UoW) -> AuthService:
    return AuthService(uow)


def get_audit_service(uow: UoW) -> AuditService:
    return AuditService(uow)