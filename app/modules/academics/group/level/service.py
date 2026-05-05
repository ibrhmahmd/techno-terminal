"""
app/modules/academics/services/group_level_service.py
────────────────────────────────────────────────────
Service class for Group Level (OTS) management.
"""

from datetime import date
from typing import List, Optional

from app.db.connection import get_session
from app.modules.academics.models import Group, GroupLevel, Course
import app.modules.academics.group.level.repository as repo
from app.modules.academics.group.level.schemas import (
    GroupLevelReadDTO,
    GroupLevelDetailDTO,
)
from app.modules.hr.models import Employee
from app.modules.academics.constants import DEFAULT_SESSIONS_PER_LEVEL
from app.shared.datetime_utils import utc_now


class GroupLevelService:
    """Service for managing immutable group level snapshots."""

    def get_level_by_number(
        self, group_id: int, level_number: int
    ) -> GroupLevelDetailDTO:
        """
        Get detailed level information including course and instructor names.

        Args:
            group_id: The group ID
            level_number: The level number

        Returns:
            GroupLevelDetailDTO with related entity names

        Raises:
            ValueError: If level not found
        """
        with get_session() as session:
            level = repo.get_group_level_by_number(session, group_id, level_number)
            if not level:
                raise ValueError(f"Level {level_number} not found for group {group_id}")

            # Fetch related entities for names
            course = session.get(Course, level.course_id) if level.course_id else None
            instructor = (
                session.get(Employee, level.instructor_id)
                if level.instructor_id
                else None
            )

            return GroupLevelDetailDTO(
                id=level.id,
                group_id=level.group_id,
                level_number=level.level_number,
                course_id=level.course_id,
                course_name=course.name if course else None,
                instructor_id=level.instructor_id,
                instructor_name=instructor.full_name if instructor else None,
                sessions_planned=level.sessions_planned,
                price_override=level.price_override,
                status=level.status,
                effective_from=level.effective_from,
                effective_to=level.effective_to,
                created_at=level.created_at,
            )

    def get_paginated_levels(
        self,
        group_id: int,
        status: Optional[str] = None,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[GroupLevelReadDTO], int]:
        """
        Get paginated list of levels for a group.

        Args:
            group_id: The group ID
            status: Filter by status (active, completed, cancelled)
            include_inactive: Include inactive levels
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            Tuple of (list of GroupLevelReadDTO, total count)
        """
        with get_session() as session:
            levels, total = repo.get_levels_by_group(
                session, group_id, status, include_inactive, skip, limit
            )
            return [GroupLevelReadDTO.model_validate(l) for l in levels], total

    def get_level_history(self, group_id: int) -> list[GroupLevel]:
        """Get all level snapshots for a group."""
        with get_session() as session:
            return list(
                repo.list_group_levels(session, group_id, include_inactive=True)
            )

    def update_level_instructor(
        self, group_id: int, level_number: int, instructor_id: int
    ) -> GroupLevel:
        """
        Update instructor for a specific level.
        Only allowed fields: instructor_id, price_override, status.
        """
        with get_session() as session:
            level = repo.get_group_level_by_number(session, group_id, level_number)
            if not level:
                raise ValueError(f"Level {level_number} not found for group {group_id}")

            level.instructor_id = instructor_id
            level.updated_at = utc_now()

            updated = repo.update_group_level(session, level)
            session.commit()
            session.refresh(updated)
            return updated

    def cancel_level(self, group_id: int, level_number: int) -> GroupLevel:
        """Cancel a level (admin only operation)."""
        with get_session() as session:
            level = repo.cancel_group_level(session, group_id, level_number)
            if not level:
                raise ValueError(f"Level {level_number} not found for group {group_id}")
            session.commit()
            session.refresh(level)
            return level
