"""HR Module

Human Resources management module for employee and staff account operations.
"""

# Constants
from app.modules.hr.constants import EmploymentType

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