"""
AttendanceStatsDTO - Attendance statistics for a student.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class AttendanceStatsDTO:
    """Attendance statistics across all enrollments."""
    total_sessions: int
    attended: int
    absent: int
    cancelled: int
    attendance_rate: float
