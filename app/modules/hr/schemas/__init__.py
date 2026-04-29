"""HR Schemas

Pydantic DTOs for HR module - input validation and output serialization.
"""
from .employee_schemas import (
    CreateEmployeeDTO,
    UpdateEmployeeDTO,
    EmployeeReadDTO,
)
from .staff_account_schemas import (
    StaffAccountDTO,
    CreateStaffAccountResultDTO,
    CreateEmployeeAccountDTO,
    EmployeeAccountResultDTO,
)
from .response_schemas import EmployeeListResponseDTO

__all__ = [
    # Employee DTOs
    "CreateEmployeeDTO",
    "UpdateEmployeeDTO",
    "EmployeeReadDTO",
    # Staff Account DTOs
    "StaffAccountDTO",
    "CreateStaffAccountResultDTO",
    "CreateEmployeeAccountDTO",
    "EmployeeAccountResultDTO",
    # Response DTOs
    "EmployeeListResponseDTO",
]
