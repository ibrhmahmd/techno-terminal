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

PaymentMethod: TypeAlias = Literal[
    "cash", "card", "transfer", "online",
    "ewallet", "instapay", "other",
]
PAYMENT_METHODS: list[PaymentMethod] = [
    "cash", "card", "transfer", "online",
    "ewallet", "instapay", "other",
]

# Mapping from any frontend input format (icon names, display labels, lowercase labels)
# to canonical backend storage values — case-insensitive, validated before storage.
PAYMENT_METHOD_MAP: dict[str, str] = {
    # Cash variants
    "cash": "cash",
    "payments": "cash",
    # Card (keep existing)
    "card": "card",
    # Transfer (keep existing)
    "transfer": "transfer",
    # Online (keep existing)
    "online": "online",
    # E-Wallet variants
    "ewallet": "ewallet",
    "e_wallet": "ewallet",
    "e-wallet": "ewallet",
    "account_balance_wallet": "ewallet",
    # instaPay variants
    "instapay": "instapay",
    "insta_pay": "instapay",
    "insta-pay": "instapay",
    "bolt": "instapay",
    # Other variants
    "other": "other",
    "more_horiz": "other",
}

TransactionType: TypeAlias = Literal["charge", "payment", "refund"]
PaymentType: TypeAlias = Literal["course_level", "competition", "other"]

# ── Enrollments ───────────────────────────────────────────────────────────────

# Mirrors enrollments_status_check (#150: "cancelled" was listed but the DB rejects it).
EnrollmentStatus: TypeAlias = Literal["active", "completed", "transferred", "dropped"]

PaymentStatus: TypeAlias = Literal["not_paid", "partially_paid", "paid"]
PAYMENT_STATUSES: list[PaymentStatus] = ["not_paid", "partially_paid", "paid"]

# ── Attendance ────────────────────────────────────────────────────────────────

AttendanceStatus: TypeAlias = Literal["present", "absent", "cancelled"]
ATTENDANCE_STATUSES: list[AttendanceStatus] = ["present", "absent", "cancelled"]

# ── Day Name Abbreviations ────────────────────────────────────────────────────

# Day abbreviation → canonical name mapping.
# Used by CRM student filter and Academics group filter endpoints to accept shorthand day names.
DAY_ABBREV_MAP: dict[str, str] = {
    "mon": "Monday",
    "tue": "Tuesday",
    "wed": "Wednesday",
    "thu": "Thursday",
    "thurs": "Thursday",
    "fri": "Friday",
    "sat": "Saturday",
    "sun": "Sunday",
}

