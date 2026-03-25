"""
app/modules/academics/constants.py
────────────────────────────────────
All domain constants for the Academics module.
Other modules should import shared constants from app.shared.constants.
"""
from datetime import time

# ── Scheduling Rules ──────────────────────────────────────────────────────────

SCHEDULING_START: time = time(11, 0)   # Earliest allowed class start: 11:00 AM
SCHEDULING_END:   time = time(21, 0)   # Latest allowed class end:   9:00 PM

WEEKDAYS: list[str] = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

# ── Status Literals ───────────────────────────────────────────────────────────
# These mirror the DB CHECK constraints. Always use these constants in queries
# and comparisons instead of raw string literals.

GROUP_STATUS_ACTIVE    = "active"
GROUP_STATUS_INACTIVE  = "inactive"
GROUP_STATUS_COMPLETED = "completed"

SESSION_STATUS_SCHEDULED  = "scheduled"
SESSION_STATUS_COMPLETED  = "completed"
SESSION_STATUS_CANCELLED  = "cancelled"

# ── Display Fallbacks ─────────────────────────────────────────────────────────

INSTRUCTOR_PLACEHOLDER = "Unassigned"   # Used in enriched SQL COALESCE

# ── Database Views ────────────────────────────────────────────────────────────

VIEW_COURSE_STATS = "v_course_stats"
