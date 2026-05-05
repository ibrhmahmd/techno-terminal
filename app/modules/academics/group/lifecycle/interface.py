"""
app/modules/academics/group/lifecycle/interface.py
────────────────────────────────────────
Interfaces for the Group Lifecycle slice.
"""
from typing import Protocol, runtime_checkable
from app.modules.academics.group.lifecycle.schemas import (
    CreateGroupWithLevelDTO,
    ProgressLevelDTO,
    CreateGroupLevelDTO,
    GroupCreationResult,
    LevelProgressionResult,
    GroupLevelResult,
)


@runtime_checkable
class GroupLifecycleServiceInterface(Protocol):
    """Contract for Group Lifecycle orchestration."""
    def create_group_with_first_level(self, data: CreateGroupWithLevelDTO) -> GroupCreationResult: ...
    def progress_to_next_level(self, data: ProgressLevelDTO) -> LevelProgressionResult: ...
    def add_level_to_existing_group(self, data: CreateGroupLevelDTO) -> GroupLevelResult: ...
