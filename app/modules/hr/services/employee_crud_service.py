"""Employee CRUD Service

Business logic for employee operations with strict DTO contracts.
"""
from typing import Optional

from app.modules.hr.repositories import HRUnitOfWork
from app.modules.hr.schemas import (
    CreateEmployeeDTO,
    EmployeeReadDTO,
    EmployeeListResponseDTO,
    UpdateEmployeeDTO,
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

        employee = self._uow.employees.create(dto)
        self._uow.flush()
        self._uow.commit()

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

        if dto.employment_type is not None:
            dto = self._normalize_employment_data(dto)

        updated = self._uow.employees.update(employee_id, dto)
        self._uow.flush()
        self._uow.commit()

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
        items, total = self._uow.employees.list_all(page, page_size)
        return EmployeeListResponseDTO(
            items=[EmployeeReadDTO.model_validate(e) for e in items],
            total=total,
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
        """Validate national ID and phone are unique.
        
        Args:
            dto: DTO with fields to check
            exclude_id: Optional ID to exclude (for updates)
            
        Raises:
            ConflictError: If fields are not unique
        """
        if hasattr(dto, 'national_id') and dto.national_id:
            existing = self._uow.employees.find_by_national_id(
                dto.national_id, exclude_id
            )
            if existing:
                raise ConflictError("National ID already exists")

        if hasattr(dto, 'phone') and dto.phone:
            existing = self._uow.employees.find_by_phone(dto.phone, exclude_id)
            if existing:
                raise ConflictError("Phone already exists")

        if hasattr(dto, 'email') and dto.email:
            existing = self._uow.employees.find_by_email(dto.email, exclude_id)
            if existing:
                raise ConflictError("Email already exists")

    def _normalize_employment_data(
        self, dto: CreateEmployeeDTO
    ) -> CreateEmployeeDTO:
        """Normalize employment type and contract percentage.

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

    def _normalize_update_employment_data(
        self, dto: UpdateEmployeeDTO
    ) -> UpdateEmployeeDTO:
        """Normalize update employment data.

        Args:
            dto: DTO to normalize

        Returns:
            Normalized DTO
        """
        if dto.employment_type is not None:
            if dto.employment_type != "contract":
                dto.contract_percentage = None
            elif dto.contract_percentage is None:
                dto.contract_percentage = 25.0
        return dto
