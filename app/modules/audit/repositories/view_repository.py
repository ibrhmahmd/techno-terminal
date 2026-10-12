from datetime import date

from sqlalchemy import text
from sqlmodel import Session

from app.modules.audit.schemas import ViewRows


class ViewRepository:
    """Reads the reporting views. Identifiers must already be validated by the caller."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def read(
        self,
        view: str,
        columns: list[str] | None = None,
        order_by: str | None = None,
        since_column: str | None = None,
        since: date | None = None,
    ) -> ViewRows:
        select_list = ", ".join(f'"{c}"' for c in columns) if columns else "*"
        sql = f'SELECT {select_list} FROM "{view}"'
        params: dict = {}
        if since_column and since is not None:
            sql += f' WHERE "{since_column}" >= :since'
            params["since"] = since
        if order_by:
            sql += f' ORDER BY "{order_by}" ASC'
        result = self._session.execute(text(sql), params)
        return ViewRows(
            view=view,
            columns=list(result.keys()),
            rows=[list(row) for row in result.all()],
        )
