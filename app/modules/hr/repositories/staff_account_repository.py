"""Staff Account Repository

Handles cross-module User-Employee operations.
"""

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

    def linked_users(self, employee: Employee) -> list[User]:
        """Every login linked to the employee, by either side of the link (#184).

        The staff-account flow sets ``employees.user_id`` and
        ``users.employee_id``; the invite flow sets only ``users.employee_id``.
        Pending invites (no ``supabase_uid`` yet) are included.
        """
        stmt = select(User).where(User.employee_id == employee.id)
        if employee.user_id is not None:
            stmt = select(User).where(
                (User.employee_id == employee.id) | (User.id == employee.user_id)
            )
        return list(self._session.exec(stmt).scalars().all())

    def has_account(self, employee: Employee) -> bool:
        """Whether the employee has a usable login: a registered user linked to them.

        An invite that was never accepted (no ``supabase_uid`` yet) does not count.
        """
        return any(u.supabase_uid is not None for u in self.linked_users(employee))
