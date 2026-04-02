"""
app/api/routers/attendance.py
────────────────────────────────
Attendance domain router — isolated from academics for clarity and future rate-limiting.

Prefix: /api/v1  (mounted in main.py)
Tag:    Attendance

Role policy:
  GET  → require_instructor  (instructors, admins, managers)
  POST → require_instructor

MarkAttendanceRequest body:
    { "student_statuses": { "12": "present", "13": "absent", "14": "late" } }
Keys are student IDs (as strings — JSON requirement), values are AttendanceStatus strings.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.schemas.common import ApiResponse
from app.api.dependencies import require_instructor, get_attendance_service
from app.modules.auth import User
from app.modules.attendance import (
    AttendanceService,
    SessionAttendanceRowDTO,
    MarkAttendanceResponseDTO,
)

router = APIRouter(tags=["Attendance"])


class MarkAttendanceRequest(BaseModel):
    """
    Body for POST /attendance/session/{session_id}/mark.
    student_statuses maps student_id → status string ("present" | "absent" | "late" | "excused").
    """

    student_statuses: dict[int, str]


# get session roster with attendance status
@router.get(
    "/attendance/session/{session_id}",
    response_model=ApiResponse[list[SessionAttendanceRowDTO]],
    summary="Get session roster with attendance status",
    description="Returns all enrolled students for this session with their current attendance status.",
)
def get_session_attendance(
    session_id: int,
    current_user: User = Depends(require_instructor),
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
        "Pass a dict of student_id → status. "
        "Students not in the dict are left unchanged (not set to absent)."
    ),
)
def mark_attendance(
    session_id: int,
    body: MarkAttendanceRequest,
    current_user: User = Depends(require_instructor),
    svc: AttendanceService = Depends(get_attendance_service),
):
    result = svc.mark_session_attendance(
        session_id=session_id,
        student_statuses=body.student_statuses,
        marked_by_user_id=current_user.id,
    )
    return ApiResponse(
        data=result,
        message=f"Attendance marked: {result.marked} records updated.",
    )
