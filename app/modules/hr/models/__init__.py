"""HR Models

SQLModel entities for HR module.
"""
from .employee_models import Employee, EmployeeBase, EmployeeCreate, EmployeeRead

__all__ = [
    "Employee",
    "EmployeeBase",
    "EmployeeCreate",
    "EmployeeRead",
]
