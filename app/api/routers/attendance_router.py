"""
app/api/routers/attendance.py
────────────────────────────────
Attendance domain router — isolated from academics for clarity and future rate-limiting.

Prefix: /api/v1  (mounted in main.py)
Tag:    Attendance

Role policy:
  GET  → require_admin (admin, system_admin)
  POST → require_admin

MarkAttendanceRequest body:
    { "entries": [{"student_id": 12, "status": "present"}, ...] }
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from app.api.schemas.common import ApiResponse
from app.api.dependencies import require_admin, get_attendance_service
from app.modules.auth import User
from app.modules.attendance import (
    AttendanceService,
    SessionAttendanceRowDTO,
    MarkAttendanceResponseDTO,
)
from app.modules.attendance.schemas.attendance_schemas import StudentAttendanceItem

router = APIRouter(tags=["Attendance"])


class MarkAttendanceRequest(BaseModel):
    """
    Body for POST /attendance/session/{session_id}/mark.
    Replaces dict with strictly typed list of attendance entries.
    """
    entries: list[StudentAttendanceItem] = Field(
        ...,
        min_length=1,
        description="List of student attendance entries to mark"
    )

    @field_validator('entries')
    @classmethod
    def validate_unique_students(cls, entries: list[StudentAttendanceItem]) -> list[StudentAttendanceItem]:
        """Ensure no duplicate student IDs in the request."""
        student_ids = [e.student_id for e in entries]
        if len(student_ids) != len(set(student_ids)):
            raise ValueError("Duplicate student IDs found in attendance entries")
        return entries


# get session roster with attendance status
@router.get(
    "/attendance/session/{session_id}",
    response_model=ApiResponse[list[SessionAttendanceRowDTO]],
    summary="Get session roster with attendance status",
    description="Returns all enrolled students for this session with their current attendance status.",
)
def get_session_attendance(
    session_id: int,
    current_user: User = Depends(require_admin),
    svc: AttendanceService = Depends(get_attendance_service),
):
    roster = svc.get_session_roster_with_attendance(session_id)
    return ApiResponse(data=roster)


# mark / update attendance for a session
@router.post(
    "/attendance/session/{session_id}/mark",
    response_model=ApiResponse[MarkAttendanceResponseDTO],
    summary="Mark / update attendance for a session",
    description=(
        "Bulk upsert attendance for a session. "
        "Pass a list of attendance entries. "
        "Students not in the list are left unchanged (not set to absent)."
    ),
)
def mark_attendance(
    session_id: int,
    body: MarkAttendanceRequest,
    current_user: User = Depends(require_admin),
    svc: AttendanceService = Depends(get_attendance_service),
):
    result = svc.mark_session_attendance(
        session_id=session_id,
        entries=body.entries,
        marked_by_user_id=current_user.id,
    )
    return ApiResponse(
        data=result,
        message=f"Attendance marked: {result.marked} records updated.",
    )
