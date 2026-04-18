"""
app/modules/attendance/__init__.py
───────────────────────────────────
Public API Facade for the Attendance module.
Maintains 100% backward compatibility for downstream UI imports while 
routing method resolution to the new strictly-typed OOP services.
"""

from .services.attendance_service import AttendanceService
from .models.attendance_models import Attendance
from .schemas.attendance_schemas import (
    AttendanceStatus,
    MarkAttendanceInput,
    SessionAttendanceRowDTO,
    EnrollmentAttendanceSummaryDTO,
    MarkAttendanceResponseDTO,
    SessionAttendanceRecord,
    StudentEnrollmentAttendanceDTO,
)

_attendance_svc = AttendanceService()

mark_session_attendance = _attendance_svc.mark_session_attendance
get_session_roster_with_attendance = _attendance_svc.get_session_roster_with_attendance
get_attendance_summary = _attendance_svc.get_attendance_summary

__all__ = [
    "Attendance",
    "AttendanceStatus",
    "MarkAttendanceInput",
    "SessionAttendanceRowDTO",
    "EnrollmentAttendanceSummaryDTO",
    "MarkAttendanceResponseDTO",
    "SessionAttendanceRecord",
    "StudentEnrollmentAttendanceDTO",
    "mark_session_attendance",
    "get_session_roster_with_attendance",
    "get_attendance_summary",
]
