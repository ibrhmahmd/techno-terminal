"""HR Repositories

Data access layer for HR module.
"""
from .employee_repository import EmployeeRepository
from .staff_account_repository import StaffAccountRepository

__all__ = [
    "EmployeeRepository",
    "StaffAccountRepository",
]
