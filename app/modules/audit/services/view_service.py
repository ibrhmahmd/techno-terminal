import re
from datetime import date

from app.db.uow import UnitOfWork
from app.modules.audit.constants import ALLOWED_VIEWS, AUDIT_DATE_COLUMNS
from app.modules.audit.repositories import ViewRepository
from app.modules.audit.schemas import ViewRows
from app.shared.exceptions import ValidationError

_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")


class AuditViewService:
    """Read access to the audit, finance and BI views (ADR-0012: the views are the
    single source of truth). Every name is checked before it reaches SQL."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._views = ViewRepository(uow.session)

    def read_view(
        self,
        view: str,
        columns: list[str] | None = None,
        order_by: str | None = None,
        since: date | None = None,
    ) -> ViewRows:
        if view not in ALLOWED_VIEWS:
            raise ValidationError(f"Unknown view: {view}")
        for name in (columns or []) + ([order_by] if order_by else []):
            if not _IDENTIFIER.match(name):
                raise ValidationError(f"Invalid column name: {name}")
        since_column = AUDIT_DATE_COLUMNS.get(view) if since else None
        return self._views.read(
            view, columns, [(order_by, "asc")] if order_by else None, since_column, since
        )
