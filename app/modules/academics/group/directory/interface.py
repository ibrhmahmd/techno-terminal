"""
app/modules/academics/group/directory/interface.py
──────────────────────────────────────────────────
Protocols (Interfaces) for the Group Directory service slice.
"""
from typing import Protocol, runtime_checkable
from app.modules.academics.group.core.schemas import EnrichedGroupDTO
from app.modules.academics.group.directory.schemas import (
    GroupedGroupsResult,
    GroupFilterDTO,
    GroupFilterResultDTO,
)


@runtime_checkable
class GroupDirectoryServiceInterface(Protocol):
    """Contract for Group Directory business logic."""
    def get_all_active_groups_enriched(self) -> list[EnrichedGroupDTO]: ...
    def get_todays_groups_enriched(self) -> list[EnrichedGroupDTO]: ...
    def get_enriched_group_by_id(self, group_id: int) -> EnrichedGroupDTO | None: ...
    def get_groups_grouped(self, group_by: str, skip: int = 0, limit: int = 50, search: str | None = None) -> GroupedGroupsResult: ...
    def filter_groups(self, filters: GroupFilterDTO) -> GroupFilterResultDTO: ...
