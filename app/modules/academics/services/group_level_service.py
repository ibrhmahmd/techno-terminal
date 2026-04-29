"""
app/modules/academics/services/group_level_service.py
────────────────────────────────────────────────────
Service class for Group Level (OTS) management.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.db.connection import get_session
from app.modules.academics.models import Group, GroupLevel, Course
from app.modules.academics import repositories as repo
from app.modules.academics.schemas.group_level_schemas import GroupLevelReadDTO, GroupLevelDetailDTO
from app.modules.hr.models import Employee
from app.shared.constants import DEFAULT_SESSIONS_PER_LEVEL


class GroupLevelService:
    """Service for managing immutable group level snapshots."""

    def get_level_by_number(
        self,
        group_id: int,
        level_number: int
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
            instructor = session.get(Employee, level.instructor_id) if level.instructor_id else None
            
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
        limit: int = 50
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

    def create_level_snapshot(
        self,
        group_id: int,
        level_number: int,
        course_id: int,
        instructor_id: int | None = None,
        sessions_planned: int = DEFAULT_SESSIONS_PER_LEVEL,
        price_override: Decimal | None = None,
    ) -> GroupLevel:
        """
        Create a new immutable level snapshot for a group.
        
        Args:
            group_id: The group to create level for
            level_number: Level number (1, 2, 3, etc.)
            course_id: Course assigned to this level
            instructor_id: Instructor for this level
            sessions_planned: Number of sessions planned
            price_override: Optional price override (uses course default if None)
        
        Returns:
            The created GroupLevel record
        """
        with get_session() as session:
            # Check if level already exists
            existing = repo.get_group_level_by_number(session, group_id, level_number)
            if existing:
                raise ValueError(f"Level {level_number} already exists for group {group_id}")
            
            level = GroupLevel(
                group_id=group_id,
                level_number=level_number,
                course_id=course_id,
                instructor_id=instructor_id,
                sessions_planned=sessions_planned,
                price_override=price_override,
                status="active",
                effective_from=datetime.utcnow(),
            )
            
            created = repo.create_group_level(session, level)
            session.commit()
            session.refresh(created)
            return created

    def complete_current_level(self, group_id: int) -> tuple[GroupLevel, GroupLevel]:
        """
        Complete the current level and create next level snapshot.
        
        Args:
            group_id: The group to progress
        
        Returns:
            Tuple of (completed_level, new_level)
        """
        with get_session() as session:
            # Get current active level
            current = repo.get_current_group_level(session, group_id)
            if not current:
                raise ValueError(f"No active level found for group {group_id}")
            
            # Complete current level
            completed = repo.complete_group_level(
                session, group_id, current.level_number
            )
            
            # Get group to access current config
            group = session.get(Group, group_id)
            if not group:
                raise ValueError(f"Group {group_id} not found")
            
            # Create next level
            next_level_number = current.level_number + 1
            course = session.get(Course, group.course_id)
            
            new_level = GroupLevel(
                group_id=group_id,
                level_number=next_level_number,
                course_id=group.course_id,
                instructor_id=group.instructor_id,
                sessions_planned=course.sessions_per_level if course else 12,
                price_override=None,
                status="active",
                effective_from=datetime.utcnow(),
            )
            
            created = repo.create_group_level(session, new_level)
            
            # Update group's level number
            group.level_number = next_level_number
            session.add(group)
            
            session.commit()
            session.refresh(completed)
            session.refresh(created)
            return completed, created

    def get_level_history(self, group_id: int) -> list[GroupLevel]:
        """Get all level snapshots for a group."""
        with get_session() as session:
            return list(repo.list_group_levels(session, group_id, include_inactive=True))

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
            level.updated_at = datetime.utcnow()
            
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
