from typing import Any

from pydantic import BaseModel


class ViewRows(BaseModel):
    """The rows of one reporting view, in column order."""

    view: str
    columns: list[str]
    rows: list[list[Any]]
