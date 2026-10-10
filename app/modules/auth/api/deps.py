"""Auth HTTP-layer service factories (ADR-0002: api/ → services/)."""

from app.api.dependencies import UoW
from app.modules.auth import AuthService, AuditService, AuthNotifier


def get_auth_service(uow: UoW) -> AuthService:
    return AuthService(uow)


def get_audit_service(uow: UoW) -> AuditService:
    return AuditService(uow)


def get_auth_notifier() -> AuthNotifier:
    """AuthNotifier provider — overridden in create_app() with the real adapter."""
    raise NotImplementedError("wired in create_app()")