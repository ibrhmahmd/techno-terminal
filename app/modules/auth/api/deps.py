"""Auth HTTP-layer service factories (ADR-0002: api/ → services/)."""

from app.modules.auth import AuthService


def get_auth_service() -> AuthService:
    return AuthService()


def get_audit_service() -> "AuditService":
    from app.modules.auth.services.audit_service import AuditService

    return AuditService()