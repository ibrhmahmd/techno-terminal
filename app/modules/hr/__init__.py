"""HR Module

Human Resources management module for employee and staff account operations.
"""

# Constants
from app.modules.hr.constants import (
    EMPLOYEE_FIELD_KEYS,
    EMPLOYEE_PAGE_SIZE,
    EmploymentType,
    EMPLOYMENT_TYPES,
    is_valid_employment_type,
)

# Models
from app.modules.hr.models import Employee, EmployeeBase

# Schemas / DTOs
from app.modules.hr.schemas import (
    CreateEmployeeDTO,
    CreateEmployeeAccountDTO,
    CreateStaffAccountResultDTO,
    EmployeeAccountResultDTO,
    EmployeeListResponseDTO,
    EmployeeReadDTO,
    StaffAccountDTO,
    StaffAccountLinkDTO,
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

# Interfaces
from app.modules.hr.services.interface import (
    EmployeeCrudServiceInterface,
    StaffAccountServiceInterface,
)
from app.modules.hr.repositories.interface import (
    EmployeeRepositoryInterface,
    StaffAccountRepositoryInterface,
)

__all__ = [
    # Constants
    "EMPLOYEE_FIELD_KEYS",
    "EMPLOYEE_PAGE_SIZE",
    "EmploymentType",
    "EMPLOYMENT_TYPES",
    "is_valid_employment_type",
    # Models
    "Employee",
    "EmployeeBase",
    # DTOs
    "CreateEmployeeDTO",
    "UpdateEmployeeDTO",
    "EmployeeReadDTO",
    "EmployeeListResponseDTO",
    "StaffAccountDTO",
    "CreateStaffAccountResultDTO",
    "CreateEmployeeAccountDTO",
    "EmployeeAccountResultDTO",
    "StaffAccountLinkDTO",
    # Interfaces
    "EmployeeCrudServiceInterface",
    "StaffAccountServiceInterface",
    "EmployeeRepositoryInterface",
    "StaffAccountRepositoryInterface",
    # Repositories
    "EmployeeRepository",
    "StaffAccountRepository",
    "HRUnitOfWork",
    # Services
    "EmployeeCrudService",
    "StaffAccountService",
]
