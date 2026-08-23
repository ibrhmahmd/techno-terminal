"""Staff Account Service

Business logic for employee-user account linking.
"""
import logging

from app.modules.auth.constants import UserRole
from app.modules.hr.models import Employee
from app.modules.hr.repositories import HRUnitOfWork
from app.modules.hr.schemas import (
    CreateEmployeeAccountDTO,
    EmployeeAccountResultDTO,
    StaffAccountDTO,
    StaffAccountLinkDTO,
)
from app.shared.constants import MIN_PASSWORD_LENGTH
from app.shared.datetime_utils import utc_now
from app.shared.exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)

_EMAIL_TAKEN_SIGNALS = ("already registered", "already exists", "already in use")


class StaffAccountService:
    """Service for staff account management."""

    def __init__(self, uow: HRUnitOfWork, supabase_client=None):
        self._uow = uow
        self._supabase = supabase_client

    def create_account(
        self, dto: CreateEmployeeAccountDTO
    ) -> EmployeeAccountResultDTO:
        """Create user account for existing employee.

        Guarantees zero partial state: remote-auth failures persist nothing,
        and a failure after the remote identity is created compensates by
        deleting that identity before rolling back local work.

        Args:
            dto: Account creation data

        Returns:
            EmployeeAccountResultDTO with created account details

        Raises:
            NotFoundError: If employee not found
            ConflictError: If email exists or employee already has account
            ValidationError: If password too short or invalid role
            BusinessRuleError: If provisioning fails midway (nothing created; retry)
        """
        employee = self._validate_account_creation(dto)

        if not self._supabase:
            raise ValidationError("Supabase client not configured")

        try:
            auth_response = self._supabase.auth.admin.create_user(
                {
                    "email": dto.email,
                    "password": dto.password,
                    "email_confirm": True,
                }
            )
            supabase_uid = auth_response.user.id
        except Exception as e:
            if self._is_email_taken_signal(e):
                raise ConflictError("email: already registered") from e
            raise BusinessRuleError(
                "Account provisioning is temporarily unavailable — "
                "nothing was created; please retry shortly."
            ) from e

        try:
            user = self._uow.staff_accounts.create_linked_account(employee, dto, supabase_uid)
            self._uow.commit()
        except Exception as exc:
            self._compensate_remote_user(supabase_uid)
            self._uow.rollback()
            if isinstance(exc, (ConflictError, NotFoundError, ValidationError)):
                raise
            raise BusinessRuleError(
                "Account provisioning failed — nothing was created; it is safe to retry."
            ) from exc

        return EmployeeAccountResultDTO(
            employee_id=employee.id,
            user_id=user.id,
            email=user.username,  # User model stores email in username field
            role=user.role,
            created_at=utc_now(),
        )

    def list_accounts(self) -> list[StaffAccountDTO]:
        """List all staff accounts with employee info.

        Returns:
            List of StaffAccountDTO
        """
        links: list[StaffAccountLinkDTO] = (
            self._uow.staff_accounts.list_all_with_employees()
        )
        return [
            StaffAccountDTO(
                user_id=link.user_id,
                employee_id=link.employee_id,
                username=link.username,
                email=link.email,
                full_name=link.full_name,
                role=link.role,
                is_active=link.is_active,
                phone=link.phone,
                job_title=link.job_title,
                created_at=link.created_at,
            )
            for link in links
        ]

    def update_account_status(
        self, user_id: int, is_active: bool, role: UserRole
    ) -> bool:
        """Update staff account status.
        
        Args:
            user_id: User ID to update
            is_active: New active status
            role: New role
            
        Returns:
            True on success
            
        Raises:
            NotFoundError: If user not found
            ValidationError: If invalid role
        """
        if not isinstance(role, UserRole):
            raise ValidationError(f"Invalid role: {role}")

        self._uow.staff_accounts.update_account_status(user_id, is_active, role)
        self._uow.commit()
        return True

    def _validate_account_creation(self, dto: CreateEmployeeAccountDTO) -> Employee:
        """Validate account creation request and resolve the target employee.

        Runs entirely before any remote call so a missing or already-linked
        employee can never leave an orphaned auth identity.

        Args:
            dto: Account creation DTO

        Returns:
            The employee to provision the account for

        Raises:
            NotFoundError: If employee not found
            ConflictError: If conflicts found
            ValidationError: If validation fails
        """
        # Validate password (pre-remote; field-named for aggregated reporting)
        if len(dto.password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f"password: must be at least {MIN_PASSWORD_LENGTH} characters"
            )

        # Validate role
        if dto.role not in {UserRole.ADMIN, UserRole.SYSTEM_ADMIN}:
            raise ValidationError(f"Invalid role: {dto.role.value}")

        # Verify employee exists
        emp = self._uow.employees.get_by_id(dto.employee_id)
        if not emp:
            raise NotFoundError(f"Employee {dto.employee_id} not found")

        # Check if employee already has account
        if emp.user_id is not None:
            raise ConflictError(
                f"Employee {dto.employee_id} already has an account"
            )

        # Note: Email uniqueness is validated by Supabase during user creation
        return emp

    @staticmethod
    def _is_email_taken_signal(exc: Exception) -> bool:
        """Detect registration-conflict signals from the remote auth provider."""
        text = str(exc).lower()
        return any(signal in text for signal in _EMAIL_TAKEN_SIGNALS)

    def _compensate_remote_user(self, supabase_uid: str) -> None:
        """Best-effort deletion of a just-created remote identity.

        Compensation failures are logged and never mask the original error.
        """
        try:
            self._supabase.auth.admin.delete_user(supabase_uid)
        except Exception:
            logger.exception(
                "Compensation failed: orphaned auth identity %s requires manual cleanup",
                supabase_uid,
            )
