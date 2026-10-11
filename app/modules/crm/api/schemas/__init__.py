"""
app/modules/crm/api/schemas/__init__.py
──────────────────────────────────────
CRM HTTP request/response schemas (moved from app/api/schemas/crm/ and app/api/schemas/students/).
"""
# From app/api/schemas/crm/
from .student import StudentPublic, StudentListingDTO, WaitingStudentDTO, StudentDeletionResult
from .parent import ParentPublic, ParentListItem
from .student_details import (
    StudentWithDetails,
    SiblingInfo,
    ParentInfo,
    EnrollmentInfo,
    StudentBalanceSummary,
)
from .activity import (
    ActivityReferenceDTO,
    ActivityActorDTO,
    ActivityLogResponseDTO,
    RecentActivityItemDTO,
    ManualActivityResponseDTO,
    ActivitySearchResultItemDTO,
)
from .history import (
    ActivityType,
    ReferenceType,
    ActivityLogRequest,
    ActivityLogUpdateRequest,
    EnrollmentHistoryEntry,
    StatusHistoryEntry,
    CompetitionHistoryEntry,
    ActivitySummaryItem,
    ActivitySearchParams,
)

# From app/api/schemas/students/ (renamed to student_activity.py, student_history.py)
from .student_activity import (
    ActivityActorDTO as StudentActivityActorDTO,
    ActivityReferenceDTO as StudentActivityReferenceDTO,
    ActivityLogResponseDTO as StudentActivityLogResponseDTO,
    ActivitySearchResultDTO,
    ActivityTypeSummaryDTO,
    ActivityTimelineResponseDTO,
    ActivitySearchResultItemDTO as StudentActivitySearchResultItemDTO,
    RecentActivityItemDTO as StudentRecentActivityItemDTO,
    ManualActivityResponseDTO as StudentManualActivityResponseDTO,
    StudentHistoryItemDTO,
    ActivityTimelineItemDTO,
)
from .student_history import (
    ActivityLogRequest as StudentActivityLogRequest,
    ActivityTimelineFilterParams,
    EnrollmentHistoryEntry as StudentEnrollmentHistoryEntry,
    ActivitySummaryItem as StudentActivitySummaryItem,
    ActivitySearchParams as StudentActivitySearchParams,
)

__all__ = [
    # From crm/student.py
    "StudentPublic",
    "StudentListingDTO",
    "WaitingStudentDTO",
    "StudentDeletionResult",
    # From crm/parent.py
    "ParentPublic",
    "ParentListItem",
    # From crm/student_details.py
    "StudentWithDetails",
    "SiblingInfo",
    "ParentInfo",
    "EnrollmentInfo",
    "StudentBalanceSummary",
    # From crm/activity.py
    "ActivityReferenceDTO",
    "ActivityActorDTO",
    "ActivityLogResponseDTO",
    "RecentActivityItemDTO",
    "ManualActivityResponseDTO",
    "ActivitySearchResultItemDTO",
    # From crm/history.py
    "ActivityType",
    "ReferenceType",
    "ActivityLogRequest",
    "ActivityLogUpdateRequest",
    "EnrollmentHistoryEntry",
    "StatusHistoryEntry",
    "CompetitionHistoryEntry",
    "ActivitySummaryItem",
    "ActivitySearchParams",
    # From students/activity.py (renamed student_activity.py)
    "StudentActivityActorDTO",
    "StudentActivityReferenceDTO",
    "StudentActivityLogResponseDTO",
    "ActivitySearchResultDTO",
    "ActivityTypeSummaryDTO",
    "ActivityTimelineResponseDTO",
    "StudentActivitySearchResultItemDTO",
    "StudentRecentActivityItemDTO",
    "StudentManualActivityResponseDTO",
    "StudentHistoryItemDTO",
    "ActivityTimelineItemDTO",
    # From students/history.py (renamed student_history.py)
    "StudentActivityLogRequest",
    "ActivityTimelineFilterParams",
    "StudentEnrollmentHistoryEntry",
    "StudentActivitySummaryItem",
    "StudentActivitySearchParams",
]