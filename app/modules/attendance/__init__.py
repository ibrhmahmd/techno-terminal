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


def __getattr__(name: str):
    """Load ``AttendanceService`` on first access.

    Lower modules (academics, crm) import ``app.modules.attendance.models``, which runs this
    package's ``__init__``. Importing the service eagerly pulls in enrollments, which imports
    academics' facade while academics is still initialising. Resolving the service lazily
    keeps ``import app.modules.academics`` (and every other entry point) order-independent.
    """
    if name == "AttendanceService":
        from app.modules.attendance.services.attendance_service import AttendanceService

        return AttendanceService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
