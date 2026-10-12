"""audit HTTP-layer service factories (ADR-0002: api/ -> services/). Read-only: never commits."""

from app.api.deps import UoW
from app.modules.audit.services import AuditService


def get_audit_service(uow: UoW) -> AuditService:
    return AuditService(uow)
