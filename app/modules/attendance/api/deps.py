"""Attendance HTTP-layer service factories (ADR-0002: api/ → services/)."""

from app.api.dependencies import UoW
from app.modules.attendance import AttendanceService


def get_attendance_service(uow: UoW) -> AttendanceService:
    return AttendanceService(uow)
