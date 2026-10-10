"""Staff Account Repository

Handles cross-module User-Employee operations.
"""
from typing import Optional

from sqlalchemy import select
from sqlmodel import Session

from app.modules.auth.models.auth_models import User
from app.modules.hr.models import Employee
from app.modules.hr.schemas import StaffAccountLinkDTO


class StaffAccountRepository:
    """Repository for staff account (User-Employee linking) operations."""

    def __init__(self, session: Session):
        self._session = session

    def list_all_with_employees(self) -> list[StaffAccountLinkDTO]:
        """List all user-employee linked accounts.

        Soft-deleted employees are excluded: their logins are blocked and
        the accounts must not surface in the staff overview.

        Returns:
            List of StaffAccountLinkDTO with user and employee data
        """
        stmt = (
            select(User, Employee)
            .join(Employee, User.employee_id == Employee.id)
            .where(Employee.deleted_at.is_(None))
        )
        results = self._session.exec(stmt).all()

        return [
            StaffAccountLinkDTO(
                user_id=user.id,
                username=user.username,
                email=user.username,  # User model stores the account email in username
                employee_id=employee.id,
                full_name=employee.full_name,
                role=user.role,
                is_active=user.is_active,
                phone=employee.phone,
                job_title=employee.job_title,
                created_at=user.created_at,
            )
            for user, employee in results
        ]

    def sync_employee_active(self, user_id: int, is_active: bool) -> None:
        """Sync employee's is_active status with linked user.

        Args:
            user_id: User ID to check for linked employee
            is_active: New active status to apply to employee if linked
        """
        user = self._session.get(User, user_id)
        if user and user.employee_id:
            emp = self._session.get(Employee, user.employee_id)
            if emp:
                emp.is_active = is_active
                self._session.add(emp)
