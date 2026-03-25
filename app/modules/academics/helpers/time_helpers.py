"""
app/modules/academics/helpers/time_helpers.py
──────────────────────────────────────────────
Pure time/date utility functions for the Academics module.
No imports from service or repository layers (clean dependency direction).
"""
from datetime import date, time, timedelta
from app.modules.academics.constants import SCHEDULING_START, SCHEDULING_END, WEEKDAYS
from app.shared.exceptions import ValidationError


def fmt_12h(t: time) -> str:
    """Formats a time object as 12-hour (e.g., 2:30 PM)."""
    h12 = t.hour % 12 or 12
    ampm = "PM" if t.hour >= 12 else "AM"
    return f"{h12}:{t.minute:02d} {ampm}"


def next_weekday(from_date: date, day_name: str) -> date:
    """Returns the next occurrence of the given weekday from from_date (inclusive)."""
    target = WEEKDAYS.index(day_name)
    delta = (target - from_date.weekday()) % 7
    return from_date + timedelta(days=delta)


def validate_times(start_time: time, end_time: time) -> None:
    """
    Raises ValidationError if start/end times fall outside the scheduling window
    (SCHEDULING_START – SCHEDULING_END) or if end <= start.
    Used by ScheduleGroupInput validator and service group scheduling.
    """
    if start_time < SCHEDULING_START or end_time > SCHEDULING_END:
        raise ValidationError(
            f"Groups must be scheduled between {fmt_12h(SCHEDULING_START)} "
            f"and {fmt_12h(SCHEDULING_END)}. "
            f"Got {fmt_12h(start_time)} – {fmt_12h(end_time)}."
        )
    if start_time >= end_time:
        raise ValidationError("End time must be after start time.")
