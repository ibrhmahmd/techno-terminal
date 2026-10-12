"""The demo UI's only data access: the audit services over a short read-only unit of work."""

from datetime import date

import pandas as pd

from app.db.uow import unit_of_work
from app.modules.audit.services import AuditViewService


def query_view(
    view: str,
    columns: list[str] | None = None,
    order_by: str | None = None,
    since: date | None = None,
) -> pd.DataFrame:
    with unit_of_work() as uow:
        result = AuditViewService(uow).read_view(view, columns, order_by, since)
    return pd.DataFrame(result.rows, columns=result.columns)
