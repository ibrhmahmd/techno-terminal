"""
app/modules/academics/constants.py
────────────────────────────────────
All domain constants for the Academics module.
Other modules should import shared constants from app.shared.constants.
"""

from datetime import time
from typing import Literal, TypeAlias

# ── Scheduling Rules ──────────────────────────────────────────────────────────

SCHEDULING_START: time = time(11, 0)  # Earliest allowed class start: 11:00 AM
SCHEDULING_END: time = time(21, 0)  # Latest allowed class end:   9:00 PM

WEEKDAYS: list[str] = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

# ── Domain Types ──────────────────────────────────────────────────────────────
GroupStatus: TypeAlias = Literal["active", "inactive", "archived"]
GROUP_STATUSES: list[GroupStatus] = ["active", "inactive", "archived"]

DEFAULT_SESSIONS_PER_LEVEL: int = 5

# ── Status Literals ───────────────────────────────────────────────────────────
# These mirror the DB CHECK constraints. Always use these constants in queries
# and comparisons instead of raw string literals.

GROUP_STATUS_ACTIVE = "active"
GROUP_STATUS_INACTIVE = "inactive"
GROUP_STATUS_COMPLETED = "completed"

LEVEL_STATUS_ACTIVE = "active"
LEVEL_STATUS_COMPLETED = "completed"
LEVEL_STATUS_CANCELLED = "cancelled"

SESSION_STATUS_SCHEDULED = "scheduled"
SESSION_STATUS_COMPLETED = "completed"
SESSION_STATUS_CANCELLED = "cancelled"

ENROLLMENT_STATUS_ACTIVE = "active"
ENROLLMENT_STATUS_COMPLETED = "completed"
ENROLLMENT_STATUS_DROPPED = "dropped"

PAYMENT_STATUS_PAID = "paid"
PAYMENT_STATUS_DUE = "due"

TRANSACTION_TYPE_PAYMENT = "payment"
TRANSACTION_TYPE_REFUND = "refund"

# ── Display Fallbacks ─────────────────────────────────────────────────────────

INSTRUCTOR_PLACEHOLDER = "Unassigned"  # Used in enriched SQL COALESCE

# ── Database Views ────────────────────────────────────────────────────────────

VIEW_COURSE_STATS = "v_course_stats"
