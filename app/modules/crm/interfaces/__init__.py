"""
CRM Module Interfaces

Re-exports DTOs.
DTOs are defined in separate files in the dtos/ subdirectory.
"""
# Re-export DTOs from separate files
from .dtos import (
    StudentSummaryDTO,
    StudentGroupedResultDTO,
    StudentGroupBucketDTO,
    StudentBalanceSummaryDTO,
    AttendanceStatsDTO,
)

__all__ = [
    # DTOs
    "StudentSummaryDTO",
    "StudentGroupedResultDTO",
    "StudentGroupBucketDTO",
    "StudentBalanceSummaryDTO",
    "AttendanceStatsDTO",
]
