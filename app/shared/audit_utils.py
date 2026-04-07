"""
Helpers for consistent created_at / updated_at / created_by stamping (D4).
"""
from __future__ import annotations

from app.shared.datetime_utils import utc_now


def apply_create_audit(obj: object, *, user_id: int | None = None) -> None:
    """Stamp new rows: created_at, updated_at where present; optional created_by."""
    t = utc_now()
    if hasattr(obj, "created_at"):
        obj.created_at = t
    if hasattr(obj, "updated_at"):
        obj.updated_at = t
    if user_id is not None and hasattr(obj, "created_by"):
        obj.created_by = user_id


def apply_update_audit(obj: object) -> None:
    """Bump updated_at on mutable rows when the model exposes it."""
    if hasattr(obj, "updated_at"):
        obj.updated_at = utc_now()
