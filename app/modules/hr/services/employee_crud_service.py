"""Employee CRUD Service

Business logic for employee operations with strict DTO contracts.
"""
from typing import Optional

from sqlalchemy.exc import IntegrityError

from app.modules.hr.repositories import HRUnitOfWork
from app.modules.hr.schemas import (
    CreateEmployeeDTO,
    EmployeeReadDTO,
    EmployeeListResponseDTO,
    UpdateEmployeeDTO,
)
from app.modules.hr.services.integrity_error_mapper import (
    translate_employee_integrity_error,
)
from app.shared.exceptions import ConflictError, NotFoundError


class EmployeeCrudService:
    """Service for employee CRUD operations."""

    def __init__(self, uow: HRUnitOfWork):
        self._uow = uow

    def create(self, dto: CreateEmployeeDTO) -> EmployeeReadDTO:
        """Create new employee.
        
        Args:
            dto: CreateEmployeeDTO with employee data
            
        Returns:
            EmployeeReadDTO of created employee
            
        Raises:
            ConflictError: If national ID or phone already exists
        """
        self._validate_unique_fields(dto)
        dto = self._normalize_employment_data(dto)

        try:
            employee = self._uow.employees.create(dto)
            self._uow.flush()
            self._uow.commit()
        except IntegrityError as exc:
            self._uow.rollback()
            raise translate_employee_integrity_error(exc) from exc

        return EmployeeReadDTO.model_validate(employee)

    def update(self, employee_id: int, dto: UpdateEmployeeDTO) -> EmployeeReadDTO:
        """Update existing employee.
        
        Args:
            employee_id: ID of employee to update
            dto: UpdateEmployeeDTO with partial data
            
        Returns:
            EmployeeReadDTO of updated employee
            
        Raises:
            NotFoundError: If employee not found
            ConflictError: If unique fields conflict
        """
        existing = self._uow.employees.get_by_id(employee_id)
        if not existing:
            raise NotFoundError(f"Employee {employee_id} not found")

        self._validate_unique_fields(dto, exclude_id=employee_id)
        self._normalize_update_employment(dto, existing)

        try:
            updated = self._uow.employees.update(employee_id, dto)
            # FR-011: deactivating an employee blocks their linked login.
            if (
                getattr(dto, "model_fields_set", set())
                & {"is_active"}
                and dto.is_active is False
                and existing.user_id is not None
            ):
                self._uow.staff_accounts.set_user_active(existing.user_id, False)
            self._uow.flush()
            self._uow.commit()
        except IntegrityError as exc:
            self._uow.rollback()
            raise translate_employee_integrity_error(exc) from exc

        return EmployeeReadDTO.model_validate(updated)

    def get_by_id(self, employee_id: int) -> EmployeeReadDTO:
        """Get employee by ID.
        
        Args:
            employee_id: Employee ID
            
        Returns:
            EmployeeReadDTO
            
        Raises:
            NotFoundError: If employee not found
        """
        emp = self._uow.employees.get_by_id(employee_id)
        if not emp:
            raise NotFoundError(f"Employee {employee_id} not found")
        return EmployeeReadDTO.model_validate(emp)

    def list_paginated(
        self, page: int = 1, page_size: int = 20
    ) -> EmployeeListResponseDTO:
        """List employees with pagination.
        
        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            EmployeeListResponseDTO with paginated results
        """
        result = self._uow.employees.list_all(page, page_size)
        return EmployeeListResponseDTO(
            items=[EmployeeReadDTO.model_validate(e) for e in result.items],
            total=result.total,
            page=page,
            page_size=page_size,
        )

    def list_active(self) -> list[EmployeeReadDTO]:
        """List all active employees.
        
        Returns:
            List of EmployeeReadDTO
        """
        employees = self._uow.employees.list_active()
        return [EmployeeReadDTO.model_validate(e) for e in employees]

    def _validate_unique_fields(
        self, dto: CreateEmployeeDTO, exclude_id: Optional[int] = None
    ) -> None:
        """Validate national ID, phone, and email uniqueness.

        Every colliding field is reported together in a single error so the
        admin sees all problems at once instead of one per attempt.

        Args:
            dto: DTO with fields to check
            exclude_id: Optional ID to exclude (for updates)

        Raises:
            ConflictError: If any field collides with an existing employee
        """
        conflicts: list[str] = []

        if dto.national_id:
            existing = self._uow.employees.find_by_national_id(
                dto.national_id, exclude_id
            )
            if existing:
                conflicts.append("national_id: already in use")

        if dto.phone:
            existing = self._uow.employees.find_by_phone(dto.phone, exclude_id)
            if existing:
                conflicts.append("phone: already in use")

        if dto.email:
            existing = self._uow.employees.find_by_email(dto.email, exclude_id)
            if existing:
                conflicts.append("email: already in use")

        if conflicts:
            raise ConflictError("; ".join(conflicts))

    def _normalize_employment_data(
        self, dto: CreateEmployeeDTO
    ) -> CreateEmployeeDTO:
        """Normalize employment type and contract percentage on create.

        Args:
            dto: DTO to normalize

        Returns:
            Normalized DTO
        """
        if dto.employment_type != "contract":
            dto.contract_percentage = None
        elif dto.contract_percentage is None:
            dto.contract_percentage = 25.0
        return dto

    def _normalize_update_employment(
        self,
        dto: UpdateEmployeeDTO,
        existing,
    ) -> None:
        """Normalize employment data on partial update in place.

        Runs whenever employment fields are touched so the DB CHECK constraint
        (`employees_contract_pct_check`) can never be violated:

        - Effective type is the incoming value when provided, else the stored one.
        - Non-contract employees never keep a contract percentage (explicit clear).
        - Switching to contract without a percentage applies the 25% default.

        Args:
            dto: Partial update DTO; mutated in place
            existing: Current Employee entity
        """
        employment_touched = (
            dto.model_fields_set & {"employment_type", "contract_percentage"}
        )
        if not employment_touched:
            return

        effective_type = (
            dto.employment_type
            if dto.employment_type is not None
            else existing.employment_type
        )

        if effective_type != "contract":
            dto.contract_percentage = None
        elif dto.contract_percentage is None:
            dto.contract_percentage = 25.0
