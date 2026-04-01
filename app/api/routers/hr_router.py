"""
app/api/routers/hr.py
──────────────────────
HR domain router (Stub Phase 5).

Prefix: /api/v1 (mounted in main.py)
Tag:    HR
"""
from typing import Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.schemas.common import ApiResponse
from app.api.dependencies import require_admin
from app.modules.auth import User

# For the stub, we import list_all_employees just to satisfy a read endpoint
from app.modules.hr.hr_service import list_all_employees
from app.modules.hr.hr_models import Employee

router = APIRouter(tags=["HR"])


class LogAttendanceInputStub(BaseModel):
    employee_id: int
    status: str
    notes: str = ""


# list all employees
@router.get(
    "/hr/employees",
    response_model=ApiResponse[list[Any]],
    summary="List all employees",
)
def list_employees(_user: User = Depends(require_admin)):
    """
    Returns a list of all employees. Restricted to admin.
    Using Any for schema until HR DTOs are finalized.
    """
    employees = list_all_employees()
    # Simple dict conversion for the stub
    return ApiResponse(data=[
        {
            "id": e.id, 
            "full_name": e.full_name, 
            "employee_role": e.employee_role,
            "employment_type": e.employment_type
        } for e in employees
    ])


# log employee attendance
@router.post(
    "/hr/attendance/log",
    response_model=ApiResponse[Any],
    summary="Log employee attendance (Stub)",
)
def log_attendance(
    body: LogAttendanceInputStub, 
    _user: User = Depends(require_admin)
):
    """
    Placeholder endpoint for HR Attendance Logging.
    """
    return ApiResponse(
        data={"employee_id": body.employee_id, "status": body.status},
        message="HR attendance logging stub."
    )
