"""HTTP layer of the HR module (ADR-0002): routers, HTTP schemas, factories."""

from app.modules.hr.api import hr_router
from app.modules.hr.api.deps import get_employee_crud_service, get_staff_account_service
from app.modules.hr.api.schemas import (
    AttendanceLogInput,
    AttendanceLogOutput,
    CreateEmployeeAccountRequest,
    EmployeeAccountResponse,
    EmployeeCreateInput,
    EmployeeListItem,
    EmployeePublic,
    EmployeeUpdateInput,
    StaffAccountCreateInput,
    StaffAccountPublic,
    StaffAccountUpdateInput,
)

__all__ = [
    "hr_router",
    "get_employee_crud_service",
    "get_staff_account_service",
    "EmployeePublic",
    "EmployeeListItem",
    "EmployeeCreateInput",
    "EmployeeUpdateInput",
    "StaffAccountPublic",
    "StaffAccountCreateInput",
    "StaffAccountUpdateInput",
    "AttendanceLogInput",
    "AttendanceLogOutput",
    "CreateEmployeeAccountRequest",
    "EmployeeAccountResponse",
]