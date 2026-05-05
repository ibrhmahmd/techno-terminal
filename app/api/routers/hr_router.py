"""
app/api/routers/hr.py
──────────────────────
HR domain router using SOLID architecture.

Prefix: /api/v1 (mounted in main.py)
Tag:    HR
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.schemas.common import ApiResponse
from app.api.schemas.hr.employee import EmployeePublic, EmployeeListItem, EmployeeCreateInput, StaffAccountPublic
from app.api.schemas.hr.employee_account import CreateEmployeeAccountRequest, EmployeeAccountResponse
from app.api.schemas.hr.attendance import AttendanceLogInput, AttendanceLogOutput

# HR SOLID services
from app.modules.hr import (
    EmployeeCrudService,
    StaffAccountService,
    CreateEmployeeDTO,
    UpdateEmployeeDTO,
    CreateEmployeeAccountDTO,
    EmployeeReadDTO,
    StaffAccountDTO,
)
from app.shared.exceptions import NotFoundError, ConflictError, ValidationError
from app.api.dependencies import require_admin, get_employee_crud_service, get_staff_account_service
from app.modules.auth import User

router = APIRouter(tags=["HR"])



# list all employees (paginated)
@router.get(
    "/hr/employees",
    response_model=ApiResponse[list[EmployeeListItem]],
    summary="List all employees",
)
def list_employees(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    _user: User = Depends(require_admin),
    service: EmployeeCrudService = Depends(get_employee_crud_service),
):
    """
    Returns a paginated list of all employees. Restricted to admin.
    """
    result = service.list_paginated(page, page_size)
    return ApiResponse(
        data=[EmployeeListItem.model_validate(e) for e in result.items],
        message=f"Showing {len(result.items)} of {result.total} employees"
    )


# get employee by ID
@router.get(
    "/hr/employees/{employee_id}",
    response_model=ApiResponse[EmployeePublic],
    summary="Get employee by ID",
)
def get_employee(
    employee_id: int,
    _user: User = Depends(require_admin),
    service: EmployeeCrudService = Depends(get_employee_crud_service),
):
    """
    Returns a single employee by ID. Restricted to admin.
    """
    try:
        emp = service.get_by_id(employee_id)
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
    service: EmployeeCrudService = Depends(get_employee_crud_service),
):
    """
    Creates a new employee record. Restricted to admin.
    """
    try:
        # Map API input to internal DTO
        dto = CreateEmployeeDTO(**body.model_dump())
        emp = service.create(dto)
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
    service: EmployeeCrudService = Depends(get_employee_crud_service),
):
    """
    Updates an existing employee record. Restricted to admin.
    """
    try:
        # Map API input to internal DTO (partial update)
        dto = UpdateEmployeeDTO(**body.model_dump(exclude_unset=True))
        emp = service.update(employee_id, dto)
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
    service: StaffAccountService = Depends(get_staff_account_service),
):
    """
    Returns all staff accounts with linked employee info. Restricted to admin.
    """
    accounts = service.list_accounts()
    # Transform DTOs to API response shape
    typed_accounts = [
        StaffAccountPublic(
            id=acc.user_id,
            username=acc.username,
            email=None,  # Not in StaffAccountDTO, would need extension
            employee_id=acc.employee_id,
            employee_name=acc.full_name,
            job_title=None,  # Not in StaffAccountDTO
            is_active=acc.is_active,
            created_at=None,  # Not in StaffAccountDTO
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
    return ApiResponse(
        data=AttendanceLogOutput(
            employee_id=body.employee_id,
            status=body.status,
            logged_at=datetime.now(timezone.utc),
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
    service: StaffAccountService = Depends(get_staff_account_service),
):
    """
    Creates a Supabase user account for an existing employee.
    Only admin or system_admin roles are allowed.
    """
    try:
        # Map API request to internal DTO
        dto = CreateEmployeeAccountDTO(
            employee_id=employee_id,
            email=body.email,
            password=body.password,
            role=body.role,
        )
        result = service.create_account(dto)
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
