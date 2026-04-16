"""
CRM Module DTOs

All DTOs are frozen dataclasses for immutability.
Each DTO is defined in its own file with filename matching the class name in snake_case.
"""

from .student_summary_dto import StudentSummaryDTO
from .student_grouped_result_dto import StudentGroupedResultDTO
from .student_group_bucket_dto import StudentGroupBucketDTO
from .student_balance_summary_dto import StudentBalanceSummaryDTO
from .student_status_summary_dto import StudentStatusSummaryDTO
from .attendance_stats_dto import AttendanceStatsDTO
from .status_history_entry_dto import StatusHistoryEntryDTO
from .activity_log_dto import ActivityLogDTO
from .timeline_filter_dto import TimelineFilterDTO
from .activity_summary_dto import ActivitySummaryDTO
from .log_registration_dto import LogRegistrationDTO
from .log_status_change_dto import LogStatusChangeDTO
from .log_enrollment_dto import LogEnrollmentDTO
from .log_enrollment_change_dto import LogEnrollmentChangeDTO
from .log_payment_dto import LogPaymentDTO
from .log_deletion_dto import LogDeletionDTO
from .log_note_added_dto import LogNoteAddedDTO
from .log_competition_registration_dto import LogCompetitionRegistrationDTO

__all__ = [
    # Student DTOs
    "StudentSummaryDTO",
    "StudentGroupedResultDTO",
    "StudentGroupBucketDTO",
    "StudentBalanceSummaryDTO",
    "StudentStatusSummaryDTO",
    "AttendanceStatsDTO",
    "StatusHistoryEntryDTO",
    # Activity DTOs
    "ActivityLogDTO",
    "TimelineFilterDTO",
    "ActivitySummaryDTO",
    "LogRegistrationDTO",
    "LogStatusChangeDTO",
    "LogEnrollmentDTO",
    "LogEnrollmentChangeDTO",
    "LogPaymentDTO",
    "LogDeletionDTO",
    "LogNoteAddedDTO",
    "LogCompetitionRegistrationDTO",
]
