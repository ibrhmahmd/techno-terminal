"""HR Module

Human Resources management module for employee and staff account operations.
"""

# Constants
from app.modules.hr.constants import EmploymentType

# Models
from app.modules.hr.models import Employee

# Schemas / DTOs
from app.modules.hr.schemas import (
    CreateEmployeeDTO,
    CreateEmployeeAccountDTO,
    EmployeeReadDTO,
    StaffAccountDTO,
    UpdateEmployeeDTO,
)

# Services
from app.modules.hr.services import EmployeeCrudService, StaffAccountService

__all__ = [
    # Constants
    "EmploymentType",
    # Models
    "Employee",
    # DTOs
    "CreateEmployeeDTO",
    "UpdateEmployeeDTO",
    "EmployeeReadDTO",
    "CreateEmployeeAccountDTO",
    "StaffAccountDTO",
    # Services
    "EmployeeCrudService",
    "StaffAccountService",
]