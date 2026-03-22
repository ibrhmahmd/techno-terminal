"""
UTC datetime helpers — prefer these over ad hoc `datetime.utcnow()` / naive `combine()`.

- **utc_now()**: timezone-aware “now” (replaces deprecated `datetime.utcnow()`, which is naive).
- **date_at_utc_midnight()**: calendar date → start-of-day in UTC (e.g. DOB → stored datetime).
- **utc_now_iso()**: ISO string for legacy columns that still store timestamps as text.
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone

__all__ = ["utc_now", "utc_now_iso", "date_at_utc_midnight"]


def utc_now() -> datetime:
    """Current instant in UTC (`tzinfo=timezone.utc`)."""
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """`utc_now().isoformat()` — for string `created_at` fields."""
    return utc_now().isoformat()


def date_at_utc_midnight(d: date) -> datetime:
    """Midnight at the start of `d` in UTC (aware datetime)."""
    return datetime.combine(d, time.min, tzinfo=timezone.utc)
