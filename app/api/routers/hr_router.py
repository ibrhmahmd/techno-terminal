"""
app/api/routers/hr.py
──────────────────────
HR domain router (Stub Phase 5).

Prefix: /api/v1 (mounted in main.py)
Tag:    HR
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.schemas.common import ApiResponse
from app.api.schemas.hr.employee import EmployeePublic, EmployeeListItem, EmployeeCreateInput, StaffAccountPublic
from app.api.schemas.hr.employee_account import CreateEmployeeAccountRequest, EmployeeAccountResponse
from app.modules.hr.hr_models import EmployeeCreate
from app.modules.hr import hr_repository as hr_repo
from app.shared.exceptions import NotFoundError, ConflictError, ValidationError
from app.api.dependencies import require_admin, get_hr_service
from app.modules.auth import User

# Import types for annotation
from app.modules.hr.hr_models import Employee

router = APIRouter(tags=["HR"])


from app.api.schemas.hr.attendance import AttendanceLogInput, AttendanceLogOutput


# list all employees
@router.get(
    "/hr/employees",
    response_model=ApiResponse[list[EmployeeListItem]],
    summary="List all employees",
)
def list_employees(
    _user: User = Depends(require_admin),
    hr=Depends(get_hr_service),
):
    """
    Returns a list of all employees. Restricted to admin.
    """
    employees = hr.list_all_employees()
    return ApiResponse(data=[EmployeeListItem.model_validate(e) for e in employees])


# get employee by ID
@router.get(
    "/hr/employees/{employee_id}",
    response_model=ApiResponse[EmployeePublic],
    summary="Get employee by ID",
)
def get_employee(
    employee_id: int,
    _user: User = Depends(require_admin),
    hr=Depends(get_hr_service),
):
    """
    Returns a single employee by ID. Restricted to admin.
    """
    try:
        emp = hr.get_employee_by_id(employee_id)
        return ApiResponse(data=EmployeePublic.model_validate(emp))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# create employee
@router.post(
    "/hr/employees",
    response_model=ApiResponse[EmployeePublic],
    status_code=201,
    summary="Create employee record",
)
def create_employee(
    body: EmployeeCreateInput,
    _user: User = Depends(require_admin),
    hr=Depends(get_hr_service),
):
    """
    Creates a new employee record. Restricted to admin.
    """
    try:
        emp_in = EmployeeCreate(**body.model_dump())
        emp = hr.create_employee_only(emp_in)
        return ApiResponse(
            data=EmployeePublic.model_validate(emp),
            message="Employee created successfully.",
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


# update employee
@router.put(
    "/hr/employees/{employee_id}",
    response_model=ApiResponse[EmployeePublic],
    summary="Update employee record",
)
def update_employee(
    employee_id: int,
    body: EmployeeCreateInput,
    _user: User = Depends(require_admin),
    hr=Depends(get_hr_service),
):
    """
    Updates an existing employee record. Restricted to admin.
    """
    try:
        emp_in = EmployeeCreate(**body.model_dump())
        emp = hr.update_employee_only(employee_id, emp_in)
        return ApiResponse(
            data=EmployeePublic.model_validate(emp),
            message="Employee updated successfully.",
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


# list staff accounts
@router.get(
    "/hr/staff-accounts",
    response_model=ApiResponse[list[StaffAccountPublic]],
    summary="List staff accounts",
)
def list_staff_accounts(
    _user: User = Depends(require_admin),
    hr=Depends(get_hr_service),
):
    """
    Returns all staff accounts with linked employee info. Restricted to admin.
    """
    accounts = hr.list_staff_accounts()
    # Transform raw dicts to typed DTOs
    typed_accounts = [
        StaffAccountPublic(
            id=acc.get("id", 0),
            username=acc.get("username", ""),
            email=acc.get("email"),
            employee_id=acc.get("employee_id", 0),
            employee_name=acc.get("employee_name", ""),
            job_title=acc.get("job_title"),
            is_active=acc.get("is_active", True),
            created_at=acc.get("created_at"),
        )
        for acc in accounts
    ]
    return ApiResponse(data=typed_accounts)


# log employee attendance
@router.post(
    "/hr/attendance/log",
    response_model=ApiResponse[AttendanceLogOutput],
    summary="Log employee attendance (Stub)",
)
def log_attendance(
    body: AttendanceLogInput,
    _user: User = Depends(require_admin)
):
    """
    Placeholder endpoint for HR Attendance Logging.
    In production, this would persist to attendance records.
    """
    from datetime import datetime
    return ApiResponse(
        data=AttendanceLogOutput(
            employee_id=body.employee_id,
            status=body.status,
            logged_at=datetime.utcnow(),
            message="Attendance logged (stub mode - not persisted).",
        ),
        message="HR attendance logging stub completed."
    )


# create employee account
@router.post(
    "/hr/employees/{employee_id}/create-account",
    response_model=ApiResponse[EmployeeAccountResponse],
    status_code=201,
    summary="Create user account for employee",
)
def create_employee_account_endpoint(
    employee_id: int,
    body: CreateEmployeeAccountRequest,
    _user: User = Depends(require_admin),
):
    """
    Creates a Supabase user account for an existing employee.
    Only admin or system_admin roles are allowed.
    """
    from app.modules.hr.hr_service import create_employee_account
    from app.modules.hr.interfaces.dtos import CreateEmployeeAccountDTO
    from app.shared.exceptions import NotFoundError, ConflictError, ValidationError

    try:
        # Wrap API request into service DTO
        dto = CreateEmployeeAccountDTO(
            employee_id=employee_id,
            email=body.email,
            password=body.password,
            role=body.role,
        )
        result = create_employee_account(dto)
        return ApiResponse(
            data=EmployeeAccountResponse(
                employee_id=result.employee_id,
                user_id=result.user_id,
                email=result.email,
                role=result.role,
                created_at=result.created_at,
            ),
            message="Employee account created successfully.",
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
