"""
app/modules/attendance/__init__.py
──────────────────────────────────
Attendance Module Facade (ADR-0003)

Other modules must import Attendance ONLY via this facade, except
app.modules.attendance.models which anyone may import (ADR-0004).

Exports:
- Models: Attendance
- Services: AttendanceService
- DTOs: AttendanceStatus, StudentAttendanceItem, SessionAttendanceRowDTO,
        MarkAttendanceResponseDTO
"""

from app.modules.attendance.models.attendance_models import Attendance
from app.modules.attendance.services.attendance_service import AttendanceService
from app.modules.attendance.schemas.attendance_schemas import (
    AttendanceStatus,
    MarkAttendanceResponseDTO,
    SessionAttendanceRowDTO,
    StudentAttendanceItem,
)

__all__ = [
    "Attendance",
    "AttendanceService",
    "AttendanceStatus",
    "MarkAttendanceResponseDTO",
    "SessionAttendanceRowDTO",
    "StudentAttendanceItem",
]
