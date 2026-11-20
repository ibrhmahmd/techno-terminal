"""Shared result type for the staging-only E2E purge (#218)."""
from pydantic import BaseModel, Field


class PurgeCountsDTO(BaseModel):
    """Rows deleted per table."""

    counts: dict[str, int] = Field(default_factory=dict)
