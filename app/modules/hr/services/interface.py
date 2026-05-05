"""HR Services Interface

Protocol definitions for HR service layer.
All service interfaces are runtime checkable for testing.
"""
from typing import Protocol, runtime_checkable

from app.modules.auth.constants import UserRole
from app.modules.hr.schemas import (
    CreateEmployeeDTO,
    EmployeeReadDTO,
    EmployeeListResponseDTO,
    UpdateEmployeeDTO,
    CreateEmployeeAccountDTO,
    EmployeeAccountResultDTO,
    StaffAccountDTO,
)


@runtime_checkable
class EmployeeCrudServiceInterface(Protocol):
    """Contract for employee CRUD operations."""

    def create(self, dto: CreateEmployeeDTO) -> EmployeeReadDTO: ...
    """Create new employee."""

    def update(self, employee_id: int, dto: UpdateEmployeeDTO) -> EmployeeReadDTO: ...
    """Update existing employee."""

    def get_by_id(self, employee_id: int) -> EmployeeReadDTO: ...
    """Get employee by ID."""

    def list_paginated(
        self, page: int = 1, page_size: int = 20
    ) -> EmployeeListResponseDTO: ...
    """List all employees with pagination."""

    def list_active(self) -> list[EmployeeReadDTO]: ...
    """List all active employees."""


@runtime_checkable
class StaffAccountServiceInterface(Protocol):
    """Contract for staff account management."""

    def create_account(
        self, dto: CreateEmployeeAccountDTO
    ) -> EmployeeAccountResultDTO: ...
    """Create user account for employee."""

    def list_accounts(self) -> list[StaffAccountDTO]: ...
    """List all staff accounts with linked employees."""

    def update_account_status(
        self, user_id: int, is_active: bool, role: UserRole
    ) -> bool: ...
    """Update staff account status.

    Args:
        user_id: User ID to update
        is_active: New active status
        role: New role

    Returns:
        True on success
    """
