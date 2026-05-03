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

# Supabase-backed accounts (staff provisioning, password reset)
MIN_PASSWORD_LENGTH: int = 12

# ── Finance ───────────────────────────────────────────────────────────────────

PaymentMethod: TypeAlias = Literal["cash", "card", "transfer", "online"]
PAYMENT_METHODS: list[PaymentMethod] = ["cash", "card", "transfer", "online"]

TransactionType: TypeAlias = Literal["charge", "payment", "refund"]
PaymentType: TypeAlias = Literal["course_level", "competition", "other"]

# ── Enrollments ───────────────────────────────────────────────────────────────

EnrollmentStatus: TypeAlias = Literal[
    "active", "completed", "transferred", "dropped", "cancelled"
]

PaymentStatus: TypeAlias = Literal["not_paid", "partially_paid", "paid"]
PAYMENT_STATUSES: list[PaymentStatus] = ["not_paid", "partially_paid", "paid"]

# ── Attendance ────────────────────────────────────────────────────────────────

AttendanceStatus: TypeAlias = Literal["present", "absent", "cancelled"]
ATTENDANCE_STATUSES: list[AttendanceStatus] = ["present", "absent", "cancelled"]

# ── Academics ─────────────────────────────────────────────────────────────────

GroupStatus: TypeAlias = Literal["active", "inactive", "archived"]
GROUP_STATUSES: list[GroupStatus] = ["active", "inactive", "archived"]

# Default number of sessions per group level
DEFAULT_SESSIONS_PER_LEVEL: int = 5

# ── HR / Employees ────────────────────────────────────────────────────────────

EmploymentType: TypeAlias = Literal["full_time", "part_time", "contract"]
EMPLOYMENT_TYPES: list[EmploymentType] = ["full_time", "part_time", "contract"]

_EMPLOYMENT_TYPE_SET = frozenset(EMPLOYMENT_TYPES)


def is_valid_employment_type(value: str | None) -> bool:
    return value is None or value in _EMPLOYMENT_TYPE_SET
