"""
app/modules/analytics/schemas/dashboard_schemas.py
────────────────────────────────────────────────
Data Transfer Objects (DTOs) for the Dashboard API.

Implements the lookup table pattern to eliminate data duplication
as specified in the Dashboard API Requirements.
"""

from typing import Optional
from pydantic import BaseModel


# ═════════════════════════════════════════════════════════════════════════════
# Query Result DTOs (Internal - for repository layer)
# ═════════════════════════════════════════════════════════════════════════════

class GroupSessionInfoDTO(BaseModel):
    """Query 1 result: Groups with sessions on target date."""
    group_id: int
    session_id: int
    session_date: str
    start_time: Optional[str]
    end_time: Optional[str]
    status: str
    level_number: int
    default_time_start: Optional[str]
    group_name: str


class GroupMetadataResultDTO(BaseModel):
    """Query 2 result: Container for group and instructor data."""
    groups: list["GroupInfoDTO"]
    instructors: list["InstructorInfoDTO"]


# ═════════════════════════════════════════════════════════════════════════════
# Lookup Table DTOs
# ═════════════════════════════════════════════════════════════════════════════

class InstructorInfoDTO(BaseModel):
    """Instructor metadata for lookup table (instructor_id -> InstructorInfo)."""
    id: int
    name: str


class GroupInfoDTO(BaseModel):
    """Group metadata for lookup table (group_id -> GroupInfo)."""
    id: int
    name: str
    course_name: str
    instructor_id: int
    current_level: int
    default_day: str
    default_time_start: str
    default_time_end: str
    schedule_display: str  # Formatted server-side: "Sat 3:00-4:30 PM"
    max_capacity: int
    student_count: int


# ═════════════════════════════════════════════════════════════════════════════
# Session DTOs
# ═════════════════════════════════════════════════════════════════════════════

class AttendanceRecordDTO(BaseModel):
    """Single attendance record for a student in a session."""
    student_id: int
    student_name: str
    gender: str  # "male" | "female"
    status: Optional[str]  # "present" | "absent" | "cancelled" | null


class SessionWithAttendanceDTO(BaseModel):
    """Session with optional attendance data (ALL sessions for current level)."""
    session_id: int
    session_number: int  # Sequential within level
    date: str  # "2024-01-10"
    time_start: str  # "15:00"
    time_end: str  # "16:30"
    status: str  # "scheduled" | "completed" | "cancelled"
    is_extra_session: bool
    
    # Per-session instructor (may differ from group's default instructor)
    actual_instructor_id: int
    instructor_name: Optional[str] = None
    is_substitute: bool = False
    
    # Attendance summary (simplified per user instruction)
    attendance_summary: Optional[dict] = None
    
    # Detailed attendance (when include_attendance=true)
    attendance: Optional[list[AttendanceRecordDTO]] = None


class TodaySessionDTO(BaseModel):
    """Session occurring on the target date."""
    session_id: int
    date: str  # "2024-01-15"
    time_start: str  # "15:00"
    time_end: str  # "16:30"
    status: str  # "scheduled" | "completed" | "cancelled"


# ═════════════════════════════════════════════════════════════════════════════
# Main Data Structure DTOs
# ═════════════════════════════════════════════════════════════════════════════

class StudentRosterDTO(BaseModel):
    """Student roster entry with billing status for dashboard."""
    student_id: int
    student_name: str
    gender: str  # 'male' | 'female'
    billing_status: str  # 'paid' | 'due'
    balance: float


class CurrentLevelDTO(BaseModel):
    """Current level data with all sessions for that level."""
    level_number: int
    sessions: list[SessionWithAttendanceDTO]


class ScheduledGroupDTO(BaseModel):
    """Main data structure: One per scheduled group."""
    group_id: int
    
    # Today's session info (if any)
    today_session: Optional[TodaySessionDTO] = None
    
    # Current level data (ALL sessions for this level)
    current_level: CurrentLevelDTO
    
    # Active enrollments with billing status
    roster: list[StudentRosterDTO]


class DashboardSummaryDTO(BaseModel):
    """Summary statistics for the dashboard."""
    total_groups_today: int
    total_instructors_today: int
    unique_instructor_ids: list[int]


# ═════════════════════════════════════════════════════════════════════════════
# Root Response DTO
# ═════════════════════════════════════════════════════════════════════════════

class DashboardDailyOverviewDTO(BaseModel):
    """
    Root response for GET /api/v1/dashboard/daily-overview
    
    Uses lookup table pattern to eliminate data duplication:
    - groups: Record<group_id, GroupInfo>
    - instructors: Record<instructor_id, InstructorInfo>
    - scheduled_groups: Flat array of group data
    """
    # Metadata
    date: str  # "2024-01-15"
    generated_at: str  # ISO 8601 timestamp
    cache_ttl: int  # Seconds (recommend: 300)
    
    # Lookup tables (deduplicated data)
    groups: dict[int, GroupInfoDTO]  # group_id -> GroupInfo
    instructors: dict[int, InstructorInfoDTO]  # instructor_id -> InstructorInfo
    
    # Main data: Active groups with sessions on the target date
    # - Sorted by default_time_start ASC (earliest first)
    scheduled_groups: list[ScheduledGroupDTO]
    
    # Stats
    summary: DashboardSummaryDTO
