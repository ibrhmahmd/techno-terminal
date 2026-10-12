from datetime import date

from sqlalchemy import text
from sqlmodel import Session

from app.modules.audit.schemas import ViewRows


_DIRECTIONS = {"asc": "ASC", "desc": "DESC NULLS LAST"}


class ViewRepository:
    """Reads the reporting views. Identifiers must already be validated by the caller."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def read(
        self,
        view: str,
        columns: list[str] | None = None,
        order_by: list[tuple[str, str]] | None = None,
        since_column: str | None = None,
        since: date | None = None,
        skip: int = 0,
        limit: int | None = None,
    ) -> ViewRows:
        select_list = ", ".join(f'"{c}"' for c in columns) if columns else "*"
        where, params = self._since(since_column, since)
        sql = f'SELECT {select_list} FROM "{view}"{where}'
        if order_by:
            sql += " ORDER BY " + ", ".join(f'"{c}" {_DIRECTIONS[d]}' for c, d in order_by)
        if limit is not None:
            sql += " LIMIT :limit OFFSET :skip"
            params.update(limit=limit, skip=skip)
        result = self._session.execute(text(sql), params)
        return ViewRows(
            view=view,
            columns=list(result.keys()),
            rows=[list(row) for row in result.all()],
        )

    def count(self, view: str, since_column: str | None = None, since: date | None = None) -> int:
        where, params = self._since(since_column, since)
        return self._session.execute(text(f'SELECT count(*) FROM "{view}"{where}'), params).scalar_one()

    @staticmethod
    def _since(since_column: str | None, since: date | None) -> tuple[str, dict]:
        if since_column and since is not None:
            return f' WHERE "{since_column}" >= :since', {"since": since}
        return "", {}
