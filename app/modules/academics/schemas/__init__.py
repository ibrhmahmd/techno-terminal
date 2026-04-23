"""
app/modules/academics/schemas/__init__.py
──────────────────────────────────────────
Re-exports all schema DTOs for backward compatibility.
Import from this module or from individual entity schema files.
"""
from .course_schemas import AddNewCourseInput, UpdateCourseDTO, CourseStatsDTO
from .group_schemas import (
    ScheduleGroupInput, UpdateGroupDTO, EnrichedGroupDTO, WeekDay,
    ProgressGroupLevelInput, ProgressGroupLevelResult,
)
from .session_schemas import AddExtraSessionInput, GenerateLevelSessionsInput, UpdateSessionDTO
from .group_details_schemas import (
    # Delete Level
    LevelDeleteResultDTO,
    # Lookup Tables
    CourseLookupDTO,
    InstructorLookupDTO,
    StudentLookupDTO,
    # Levels Detailed
    SessionInLevelDTO,
    PaymentSummaryDTO,
    LevelWithSessionsDTO,
    GroupLevelsDetailedResponseDTO,
    # Attendance Grid
    AttendanceRosterStudentDTO,
    AttendanceSessionDTO,
    GroupAttendanceResponseDTO,
    # Payments
    PaymentInLevelDTO,
    LevelPaymentSummaryDTO,
    GroupPaymentsSummaryDTO,
    GroupPaymentsResponseDTO,
    # Enrollments
    EnrollmentInLevelDTO,
    LevelEnrollmentSummaryDTO,
    LevelWithEnrollmentsDTO,
    TransferOptionDTO,
    GroupEnrollmentsResponseDTO,
)

__all__ = [
    # Course
    "AddNewCourseInput",
    "UpdateCourseDTO",
    "CourseStatsDTO",
    # Group
    "ScheduleGroupInput",
    "UpdateGroupDTO",
    "EnrichedGroupDTO",
    "WeekDay",
    # Group Level Management
    "ProgressGroupLevelInput",
    "ProgressGroupLevelResult",
    # Session
    "AddExtraSessionInput",
    "GenerateLevelSessionsInput",
    "UpdateSessionDTO",
    # Group Details - Delete Level
    "LevelDeleteResultDTO",
    # Group Details - Lookup Tables
    "CourseLookupDTO",
    "InstructorLookupDTO",
    "StudentLookupDTO",
    # Group Details - Levels Detailed
    "SessionInLevelDTO",
    "PaymentSummaryDTO",
    "LevelWithSessionsDTO",
    "GroupLevelsDetailedResponseDTO",
    # Group Details - Attendance Grid
    "AttendanceRosterStudentDTO",
    "AttendanceSessionDTO",
    "GroupAttendanceResponseDTO",
    # Group Details - Payments
    "PaymentInLevelDTO",
    "LevelPaymentSummaryDTO",
    "GroupPaymentsSummaryDTO",
    "GroupPaymentsResponseDTO",
    # Group Details - Enrollments
    "EnrollmentInLevelDTO",
    "LevelEnrollmentSummaryDTO",
    "LevelWithEnrollmentsDTO",
    "TransferOptionDTO",
    "GroupEnrollmentsResponseDTO",
]