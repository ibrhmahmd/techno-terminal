"""Staff Account Repository

Handles cross-module User-Employee operations.
"""
from typing import Optional, TYPE_CHECKING

from sqlalchemy import select
from sqlmodel import Session

from app.modules.hr.models import Employee
from app.modules.hr.schemas import CreateEmployeeAccountDTO
from app.shared.exceptions import NotFoundError

if TYPE_CHECKING:
    from app.modules.auth.models.auth_models import User


class StaffAccountRepository:
    """Repository for staff account (User-Employee linking) operations."""

    def __init__(self, session: Session):
        self._session = session

    def create_linked_account(
        self, employee: Employee, dto: CreateEmployeeAccountDTO, supabase_uid: str
    ) -> tuple[Employee, "User"]:
        """Create user and link to employee in one transaction.
        
        Args:
            employee: Employee to link
            dto: Account creation DTO
            supabase_uid: Supabase user UID
            
        Returns:
            Tuple of (updated Employee, created User)
        """
        # Import here to avoid circular dependency
        from app.modules.auth.models.auth_models import User
        
        user = User(
            username=dto.email,
            role=dto.role,
            supabase_uid=supabase_uid,
            is_active=True,
        )
        self._session.add(user)
        self._session.flush()

        employee.user_id = user.id
        self._session.add(employee)
        self._session.flush()

        return employee, user

    def list_all_with_employees(self) -> list[tuple["User", Employee]]:
        """List all user-employee linked accounts.
        
        Returns:
            List of (User, Employee) tuples
        """
        # Import here to avoid circular dependency
        from app.modules.auth.models.auth_models import User
        
        stmt = select(User, Employee).join(
            Employee, User.employee_id == Employee.id
        )
        return list(self._session.exec(stmt).all())

    def update_account_status(
        self, user_id: int, is_active: bool, role: str
    ) -> None:
        """Update user and linked employee status.
        
        Args:
            user_id: User ID to update
            is_active: New active status
            role: New role
            
        Raises:
            NotFoundError: If user not found
        """
        # Import here to avoid circular dependency
        from app.modules.auth.models.auth_models import User
        
        user = self._session.get(User, user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")

        user.is_active = is_active
        user.role = role

        if user.employee_id:
            emp = self._session.get(Employee, user.employee_id)
            if emp:
                emp.is_active = is_active
                self._session.add(emp)

        self._session.add(user)

    def find_user_by_username(self, username: str) -> Optional["User"]:
        """Find user by username.
        
        Args:
            username: Username to search
            
        Returns:
            User or None
        """
        from app.modules.auth.models.auth_models import User
        stmt = select(User).where(User.username == username)
        return self._session.exec(stmt).first()
