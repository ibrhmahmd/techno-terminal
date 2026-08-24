"""Employee Repository

Data access for employee entity - class-based with DTO parameters.
"""
from typing import Optional

from sqlalchemy import func, select
from sqlmodel import Session

from app.modules.hr.models import Employee
from app.modules.hr.schemas import CreateEmployeeDTO, UpdateEmployeeDTO, EmployeeListResult
from app.shared.datetime_utils import utc_now
from app.shared.exceptions import ConflictError, NotFoundError


class EmployeeRepository:
    """Repository for employee data access."""

    def __init__(self, session: Session):
        self._session = session

    def create(self, dto: CreateEmployeeDTO) -> Employee:
        """Create new employee from DTO.
        
        Args:
            dto: CreateEmployeeDTO with employee data
            
        Returns:
            Created Employee instance
        """
        emp = Employee(**dto.model_dump(exclude_unset=True))
        self._session.add(emp)
        self._session.flush()
        return emp

    def update(self, employee_id: int, dto: UpdateEmployeeDTO) -> Optional[Employee]:
        """Update employee from DTO.
        
        Args:
            employee_id: ID of employee to update
            dto: UpdateEmployeeDTO with partial data
            
        Returns:
            Updated Employee or None if not found
        """
        emp = self._session.get(Employee, employee_id)
        if not emp:
            return None

        # exclude_unset keeps partial semantics while allowing the service to
        # pass explicit None values (e.g. clearing contract_percentage).
        update_data = dto.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(emp, key, value)

        emp.updated_at = utc_now()
        self._session.add(emp)
        return emp

    def get_by_id(
        self, employee_id: int, include_deleted: bool = False
    ) -> Optional[Employee]:
        """Get employee by ID.

        Args:
            employee_id: Employee ID
            include_deleted: Return soft-deleted employees too

        Returns:
            Employee or None (deleted rows excluded unless include_deleted)
        """
        emp = self._session.get(Employee, employee_id)
        if emp and not include_deleted and emp.deleted_at is not None:
            return None
        return emp

    def soft_delete(self, employee_id: int, deleted_by: int) -> Employee:
        """Stamp soft-delete markers on a live employee.

        Args:
            employee_id: ID of the employee to delete
            deleted_by: Local user ID of the acting admin

        Returns:
            The soft-deleted Employee

        Raises:
            NotFoundError: If the employee is missing or already deleted
        """
        emp = self._session.get(Employee, employee_id)
        if not emp or emp.deleted_at is not None:
            raise NotFoundError(f"Employee {employee_id} not found")
        emp.deleted_at = utc_now()
        emp.deleted_by = deleted_by
        self._session.add(emp)
        return emp

    def restore(self, employee_id: int) -> Employee:
        """Clear soft-delete markers on a previously deleted employee.

        Args:
            employee_id: ID of the employee to restore

        Returns:
            The restored Employee

        Raises:
            NotFoundError: If no employee exists with this ID
            ConflictError: If the employee is not currently deleted
        """
        emp = self._session.get(Employee, employee_id)
        if not emp:
            raise NotFoundError(f"Employee {employee_id} not found")
        if emp.deleted_at is None:
            raise ConflictError(f"Employee {employee_id} is not deleted")
        emp.deleted_at = None
        emp.deleted_by = None
        self._session.add(emp)
        return emp

    def find_by_national_id(
        self, nid: str, exclude_id: Optional[int] = None
    ) -> Optional[Employee]:
        """Find employee by national ID.
        
        Args:
            nid: National ID to search
            exclude_id: Optional ID to exclude (for updates)
            
        Returns:
            Employee or None
        """
        stmt = select(Employee).where(
            Employee.national_id == nid.strip(),
            Employee.deleted_at.is_(None),
        )
        if exclude_id:
            stmt = stmt.where(Employee.id != exclude_id)
        return self._session.exec(stmt).first()

    def find_by_phone(
        self, phone: str, exclude_id: Optional[int] = None
    ) -> Optional[Employee]:
        """Find employee by phone.
        
        Args:
            phone: Phone number to search (digits only)
            exclude_id: Optional ID to exclude
            
        Returns:
            Employee or None
        """
        stmt = select(Employee).where(
            Employee.phone == phone,
            Employee.deleted_at.is_(None),
        )
        if exclude_id:
            stmt = stmt.where(Employee.id != exclude_id)
        return self._session.exec(stmt).first()

    def find_by_email(
        self, email: str, exclude_id: Optional[int] = None
    ) -> Optional[Employee]:
        """Find employee by email.
        
        Args:
            email: Email to search
            exclude_id: Optional ID to exclude
            
        Returns:
            Employee or None
        """
        stmt = select(Employee).where(
            Employee.email == email.strip(),
            Employee.deleted_at.is_(None),
        )
        if exclude_id:
            stmt = stmt.where(Employee.id != exclude_id)
        return self._session.exec(stmt).first()

    def list_active(self) -> list[Employee]:
        """List all active employees (soft-deleted rows never appear)."""
        stmt = select(Employee).where(
            Employee.is_active.is_(True),
            Employee.deleted_at.is_(None),
        )
        results = self._session.exec(stmt)
        return list(results.scalars().all())

    def list_all(
        self, page: int = 1, page_size: int = 20, include_deleted: bool = False
    ) -> EmployeeListResult:
        """List employees with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            include_deleted: Include soft-deleted employees (admin discovery)

        Returns:
            EmployeeListResult with paginated employees and total count
        """
        base_filter = (
            None if include_deleted else Employee.deleted_at.is_(None)
        )

        count_stmt = select(func.count()).select_from(Employee)
        if base_filter is not None:
            count_stmt = count_stmt.where(base_filter)
        total = self._session.exec(count_stmt).scalar() or 0

        offset = (page - 1) * page_size
        stmt = select(Employee).offset(offset).limit(page_size)
        if base_filter is not None:
            stmt = stmt.where(base_filter)
        results = self._session.exec(stmt)
        employees = list(results.scalars().all())

        return EmployeeListResult(items=employees, total=total)
