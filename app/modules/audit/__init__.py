"""audit module facade: integrity checks and the reporting-view reads behind the demo UI.

audit is the top module (ADR-0011); nothing imports it yet.
"""

from app.modules.audit.schemas import ViewRows
from app.modules.audit.services import AuditViewService

__all__ = ["AuditViewService", "ViewRows"]
