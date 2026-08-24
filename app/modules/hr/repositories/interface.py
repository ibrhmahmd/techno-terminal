"""HR Repositories Interface

Protocol definitions for HR repository layer.
All repository interfaces are runtime checkable for testing.
"""
from typing import Protocol, runtime_checkable, TYPE_CHECKING

from app.modules.hr.models import Employee

from app.modules.hr.schemas import (
    CreateEmployeeDTO,
    UpdateEmployeeDTO,
    CreateEmployeeAccountDTO,
    EmployeeListResult,
    StaffAccountLinkDTO,
)

if TYPE_CHECKING:
    from app.modules.auth.models.auth_models import User


@runtime_checkable
class EmployeeRepositoryInterface(Protocol):
    """Contract for employee data access."""

    def create(self, dto: CreateEmployeeDTO) -> Employee: ...
    """Create new employee from DTO."""

    def update(
        self, employee_id: int, dto: UpdateEmployeeDTO
    ) -> Employee | None: ...
    """Update employee from DTO."""

    def get_by_id(
        self, employee_id: int, include_deleted: bool = False
    ) -> Employee | None: ...
    """Get employee by ID; deleted rows excluded unless include_deleted."""

    def soft_delete(self, employee_id: int, deleted_by: int) -> Employee: ...
    """Stamp deleted_at/deleted_by markers.

    Raises:
        NotFoundError: If the employee is missing or already deleted
    """

    def restore(self, employee_id: int) -> Employee: ...
    """Clear soft-delete markers.

    Raises:
        NotFoundError: If no employee exists with this ID
        ConflictError: If the employee is not currently deleted
    """

    def list_active(self) -> list[Employee]: ...
    """List all active employees."""

    def list_all(
        self, page: int = 1, page_size: int = 20, include_deleted: bool = False
    ) -> EmployeeListResult: ...
    """List employees with pagination as a named result (items + total)."""


@runtime_checkable
class StaffAccountRepositoryInterface(Protocol):
    """Contract for staff account (User-Employee linking) operations."""

    def create_linked_account(
        self,
        employee: Employee,
        dto: CreateEmployeeAccountDTO,
        supabase_uid: str,
    ) -> "User": ...  # type: ignore[type-arg]
    """Create user and link to employee. Returns the created User."""

    def list_all_with_employees(self) -> list[StaffAccountLinkDTO]: ...
    """List all user-employee linked accounts."""

    def update_account_status(
        self, user_id: int, is_active: bool, role: str
    ) -> None: ...
    """Update user and linked employee status.

    Args:
        user_id: User ID to update
        is_active: New active status
        role: New role

    Raises:
        NotFoundError: If user not found
    """

    def set_user_active(self, user_id: int, active: bool) -> None: ...
    """Set a user account's active flag without touching role or employee.

    Args:
        user_id: User ID to update
        active: New is_active value

    Raises:
        NotFoundError: If user not found
    """

    def find_user_by_username(self, username: str) -> "User | None": ...  # type: ignore[type-arg]
    """Find user by username."""

    def find_user_by_email(self, email: str) -> "User | None": ...  # type: ignore[type-arg]
    """Find user by email."""
