"""HR Module

Human Resources management module for employee and staff account operations.
"""

# Constants
from app.modules.hr.constants import (
    EMPLOYEE_FIELD_KEYS,
    EMPLOYEE_PAGE_SIZE,
    MIN_NATIONAL_ID_LENGTH,
)

# Models
from app.modules.hr.models import Employee, EmployeeBase, EmployeeCreate, EmployeeRead

# Schemas / DTOs
from app.modules.hr.schemas import (
    CreateEmployeeDTO,
    CreateEmployeeAccountDTO,
    CreateStaffAccountResultDTO,
    EmployeeAccountResultDTO,
    EmployeeListResponseDTO,
    EmployeeReadDTO,
    StaffAccountDTO,
    UpdateEmployeeDTO,
)

# Repositories & Unit of Work
from app.modules.hr.repositories import (
    EmployeeRepository,
    HRUnitOfWork,
    StaffAccountRepository,
)

# Services
from app.modules.hr.services import EmployeeCrudService, StaffAccountService

# Validators
from app.modules.hr.validators import (
    validate_employment_type,
    validate_national_id,
    validate_phone,
)

__all__ = [
    # Constants
    "EMPLOYEE_FIELD_KEYS",
    "EMPLOYEE_PAGE_SIZE",
    "MIN_NATIONAL_ID_LENGTH",
    # Models
    "Employee",
    "EmployeeBase",
    "EmployeeCreate",
    "EmployeeRead",
    # DTOs
    "CreateEmployeeDTO",
    "UpdateEmployeeDTO",
    "EmployeeReadDTO",
    "EmployeeListResponseDTO",
    "StaffAccountDTO",
    "CreateStaffAccountResultDTO",
    "CreateEmployeeAccountDTO",
    "EmployeeAccountResultDTO",
    # Repositories
    "EmployeeRepository",
    "StaffAccountRepository",
    "HRUnitOfWork",
    # Services
    "EmployeeCrudService",
    "StaffAccountService",
    # Validators
    "validate_national_id",
    "validate_phone",
    "validate_employment_type",
]
