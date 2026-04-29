"""Employee Repository

Data access for employee entity - class-based with DTO parameters.
"""
from typing import Optional

from sqlalchemy import func, select
from sqlmodel import Session

from app.modules.hr.models import Employee
from app.modules.hr.schemas import CreateEmployeeDTO, UpdateEmployeeDTO
from app.shared.datetime_utils import utc_now


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

        update_data = dto.model_dump(exclude_unset=True, exclude_none=True)
        for key, value in update_data.items():
            setattr(emp, key, value)

        emp.updated_at = utc_now()
        self._session.add(emp)
        return emp

    def get_by_id(self, employee_id: int) -> Optional[Employee]:
        """Get employee by ID.
        
        Args:
            employee_id: Employee ID
            
        Returns:
            Employee or None
        """
        return self._session.get(Employee, employee_id)

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
        stmt = select(Employee).where(Employee.national_id == nid.strip())
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
        stmt = select(Employee).where(Employee.phone == phone)
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
        stmt = select(Employee).where(Employee.email == email.strip())
        if exclude_id:
            stmt = stmt.where(Employee.id != exclude_id)
        return self._session.exec(stmt).first()

    def list_active(self) -> list[Employee]:
        """List all active employees."""
        stmt = select(Employee).where(Employee.is_active.is_(True))
        results = self._session.exec(stmt)
        return list(results.scalars().all())

    def list_all(self, page: int = 1, page_size: int = 20) -> tuple[list[Employee], int]:
        """List all employees with pagination.
        
        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            Tuple of (employees list, total count)
        """
        # Get total count - use scalar() to get int value, not Row tuple
        total = self._session.exec(
            select(func.count()).select_from(Employee)
        ).scalar() or 0

        # Get paginated results - use scalars() to get ORM objects not Row tuples
        offset = (page - 1) * page_size
        stmt = select(Employee).offset(offset).limit(page_size)
        results = self._session.exec(stmt)
        employees = list(results.scalars().all())
        
        return employees, total
