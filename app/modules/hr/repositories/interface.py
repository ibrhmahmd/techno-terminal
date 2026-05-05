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

    def get_by_id(self, employee_id: int) -> Employee | None: ...
    """Get employee by ID."""

    def get_by_national_id(self, national_id: str) -> Employee | None: ...
    """Get employee by national ID."""

    def get_by_phone(self, phone: str) -> Employee | None: ...
    """Get employee by phone number."""

    def get_by_email(self, email: str, exclude_id: int | None = None) -> Employee | None: ...
    """Get employee by email, optionally excluding an ID."""

    def list_active(self) -> list[Employee]: ...
    """List all active employees."""

    def list_all(self, page: int = 1, page_size: int = 20) -> tuple[list[Employee], int]: ...
    """List all employees with pagination. Returns (employees, total_count)."""


@runtime_checkable
class StaffAccountRepositoryInterface(Protocol):
    """Contract for staff account (User-Employee linking) operations."""

    def create_linked_account(
        self,
        employee: Employee,
        dto: CreateEmployeeAccountDTO,
        supabase_uid: str,
    ) -> tuple[Employee, "User"]: ...  # type: ignore[type-arg]
    """Create user and link to employee."""

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

    def find_user_by_username(self, username: str) -> "User | None": ...  # type: ignore[type-arg]
    """Find user by username."""

    def find_user_by_email(self, email: str) -> "User | None": ...  # type: ignore[type-arg]
    """Find user by email."""
