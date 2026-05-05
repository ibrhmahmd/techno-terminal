"""
app/modules/academics/group/details/interface.py
────────────────────────────────────────
Interfaces for the Group Details slice.
"""
from typing import Protocol, runtime_checkable
from app.modules.academics.group.details.schemas import (
    LevelDeleteResultDTO,
    GroupLevelsDetailedResponseDTO,
    GroupAttendanceResponseDTO,
    GroupPaymentsResponseDTO,
    GroupEnrollmentsResponseDTO,
)


@runtime_checkable
class GroupDetailsServiceInterface(Protocol):
    """Contract for Group Details business logic."""
    def delete_level(self, group_id: int, level_number: int) -> LevelDeleteResultDTO: ...
    def get_levels_detailed(self, group_id: int, level_number: int | None = None) -> GroupLevelsDetailedResponseDTO: ...
    def get_attendance_grid(self, group_id: int, level_number: int) -> GroupAttendanceResponseDTO: ...
    def get_group_payments(self, group_id: int) -> GroupPaymentsResponseDTO: ...
    def get_group_enrollments(self, group_id: int) -> GroupEnrollmentsResponseDTO: ...
