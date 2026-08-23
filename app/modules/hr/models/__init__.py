"""HR Models

SQLModel entities for HR module.
"""
from .employee_models import Employee, EmployeeBase

__all__ = [
    "Employee",
    "EmployeeBase",
]
