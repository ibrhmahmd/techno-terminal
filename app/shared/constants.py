"""
app/shared/constants.py
───────────────────────
Shared type aliases and lists for domain constants.

Using `Literal` provides IDE support and static type checking.
Because SQLModel inherits from Pydantic, using these aliases in models
will AUTOMATICALLY enforce runtime validation when records are created.
"""
from typing import Literal, TypeAlias

# ── Common ────────────────────────────────────────────────────────────────────

# Shared type alias for database IDs to make intent clear in signatures
ID: TypeAlias = int

# ── Finance ───────────────────────────────────────────────────────────────────

PaymentMethod: TypeAlias = Literal["cash", "card", "transfer", "online"]
PAYMENT_METHODS: list[PaymentMethod] = ["cash", "card", "transfer", "online"]

TransactionType: TypeAlias = Literal["charge", "payment", "refund"]
PaymentType: TypeAlias = Literal["course_level", "competition", "other"]

# ── Enrollments ───────────────────────────────────────────────────────────────

EnrollmentStatus: TypeAlias = Literal[
    "active", "completed", "transferred", "dropped", "cancelled"
]

# ── Attendance ────────────────────────────────────────────────────────────────

AttendanceStatus: TypeAlias = Literal["present", "absent", "late", "excused"]
ATTENDANCE_STATUSES: list[AttendanceStatus] = ["present", "absent", "late", "excused"]

# ── Academics ─────────────────────────────────────────────────────────────────

GroupStatus: TypeAlias = Literal["active", "inactive", "completed"]
GROUP_STATUSES: list[GroupStatus] = ["active", "inactive", "completed"]
