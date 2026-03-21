"""
Canonical user roles for the application and database CHECK constraints.

To add a role later:
  1. Add a new member here and include it in ALL_ROLE_VALUES.
  2. Update the CHECK on users.role in db/schema.sql and add a db/migrations/*.sql
     (and/or an Alembic revision) to alter the constraint on existing databases.
"""
from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    SYSTEM_ADMIN = "system_admin"


ALL_ROLE_VALUES: frozenset[str] = frozenset(m.value for m in UserRole)


def is_valid_role(role: str) -> bool:
    return role in ALL_ROLE_VALUES
