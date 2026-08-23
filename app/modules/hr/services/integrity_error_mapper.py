"""IntegrityError translation for employee-table unique constraints.

Maps PostgreSQL unique-constraint violations on `employees` to typed
ConflictErrors naming the offending field, so concurrent writes race-safe
through the existing DB constraints instead of surfacing as HTTP 500s.
"""
from sqlalchemy.exc import IntegrityError

from app.shared.exceptions import ConflictError

_CONSTRAINT_FIELD_MAP = {
    "uq_employees_email": "email",
    "uq_employees_national_id": "national_id",
    "uq_employees_phone": "phone",
    "uq_employees_user_id": "user_id",
}


def translate_employee_integrity_error(exc: IntegrityError) -> ConflictError:
    """Convert an employees-table IntegrityError into a field-named ConflictError."""
    text = str(getattr(exc, "orig", exc))
    for constraint, field in _CONSTRAINT_FIELD_MAP.items():
        if constraint in text:
            return ConflictError(f"{field}: already in use")
    return ConflictError("Employee values conflict with an existing record")
