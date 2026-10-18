"""
UTC datetime helpers — prefer these over ad hoc `datetime.utcnow()` / naive `combine()`.

- **utc_now()**: timezone-aware “now” (replaces deprecated `datetime.utcnow()`, which is naive).
- **date_at_utc_midnight()**: calendar date → start-of-day in UTC (e.g. DOB → stored datetime).
- **utc_now_iso()**: ISO string for legacy columns that still store timestamps as text.
- **time_to_str()**: datetime.time → ISO format string (for API responses).
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

__all__ = [
    "CAIRO_TZ",
    "utc_now",
    "utc_now_iso",
    "date_at_utc_midnight",
    "cairo_day_bounds",
    "time_to_str",
]

CAIRO_TZ = ZoneInfo("Africa/Cairo")


def utc_now() -> datetime:
    """Current instant in UTC (`tzinfo=timezone.utc`)."""
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """`utc_now().isoformat()` — for string `created_at` fields."""
    return utc_now().isoformat()


def date_at_utc_midnight(d: date) -> datetime:
    """Midnight at the start of `d` in UTC (aware datetime)."""
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


def cairo_day_bounds(d: date) -> tuple[datetime, datetime]:
    """Aware start of `d` and start of the next day, both in Africa/Cairo."""
    start = datetime.combine(d, time.min, tzinfo=CAIRO_TZ)
    end = datetime.combine(d + timedelta(days=1), time.min, tzinfo=CAIRO_TZ)
    return start, end


def time_to_str(value) -> Optional[str]:
    """
    Convert datetime.time to ISO format string.
    
    Used by API schemas to convert database time fields to JSON-serializable strings.
    
    Args:
        value: datetime.time object or None
        
    Returns:
        ISO format string (e.g., "12:00:00") or None if input is None
        
    Example:
        >>> from datetime import time
        >>> time_to_str(time(12, 30))
        '12:30:00'
    """
    if value is None:
        return None
    if isinstance(value, time):
        return value.isoformat()
    return value
