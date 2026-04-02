"""
app/modules/auth/constants.py
──────────────────────────────
Auth-domain constants: role definitions and validators.
"""
from enum import Enum


class UserRole(str, Enum):
    """User roles for the application."""
    ADMIN = "admin"
    SYSTEM_ADMIN = "system_admin"


# Precomputed set of all valid role string values for fast O(1) membership tests.
ALL_ROLE_VALUES: frozenset[str] = frozenset(role.value for role in UserRole)


def is_valid_role(value: str) -> bool:
    """Returns True if *value* is a recognised role string."""
    return value in ALL_ROLE_VALUES
