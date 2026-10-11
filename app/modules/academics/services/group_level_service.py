"""
app/modules/academics/services/group_level_service.py
────────────────────────────────────────────────────
Service class for Group Level (OTS) management.
"""

from typing import Optional

from app.db.uow import UnitOfWork
from app.modules.academics.models import Group, GroupLevel, Course
import app.modules.academics.repositories.group_level_repository as repo
from app.modules.academics.schemas.group_level_schemas import (
    GroupLevelDetailDTO,
    UpdateLevelInput,
)
from app.modules.hr.models import Employee
from app.shared.datetime_utils import utc_now
from app.shared.audit_utils import apply_update_audit
from app.shared.exceptions import NotFoundError, BusinessRuleError


class GroupLevelService:
    """Service for managing immutable group level snapshots."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

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
        session = self._uow.session
        level = repo.get_group_level_by_number(session, group_id, level_number)
        if not level:
            raise NotFoundError(f"Level {level_number} not found for group {group_id}")

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
            notes=level.notes,
            created_at=level.created_at,
        )

    def update_level(
        self, group_id: int, level_number: int, data: UpdateLevelInput
    ) -> GroupLevelDetailDTO:
        """
        Update mutable fields of a level (active levels only).
        """

        session = self._uow.session
        # 1. Fetch level
        level = repo.get_group_level_by_number(session, group_id, level_number)
        if not level:
            raise NotFoundError(f"Level {level_number} not found for group {group_id}")

        # 2. Prevent edits on non-active levels
        if level.status != "active":
            raise BusinessRuleError(f"Cannot edit level {level_number} with status '{level.status}'")

        # 3. Apply updates
        if data.instructor_id is not None:
            # Validate instructor exists
            instructor = session.get(Employee, data.instructor_id)
            if not instructor:
                raise NotFoundError(f"Instructor {data.instructor_id} not found")
            level.instructor_id = data.instructor_id

        if data.course_id is not None:
            # Validate course exists
            course = session.get(Course, data.course_id)
            if not course:
                raise NotFoundError(f"Course {data.course_id} not found")
            level.course_id = data.course_id

        if data.price_override is not None:
            level.price_override = data.price_override

        if data.notes is not None:
            level.notes = data.notes

        session.add(level)
        self._uow.commit()

        # Re-fetch via get_level_by_number to return enriched DTO
        return self.get_level_by_number(group_id, level_number)

    def cancel_level(
        self, group_id: int, level_number: int, reason: Optional[str] = None
    ) -> GroupLevel:
        """Cancel a level (admin only operation)."""

        session = self._uow.session
        # 1. Fetch level first
        level = repo.get_group_level_by_number(session, group_id, level_number)
        if not level:
            raise NotFoundError(f"Level {level_number} not found for group {group_id}")

        # 2. Check if already completed or cancelled
        if level.status == "completed":
            raise ValueError("Cannot cancel an already completed level")
        if level.status == "cancelled":
            raise ValueError("Level is already cancelled")

        # 3. Cancel it
        level.status = "cancelled"
        level.effective_to = utc_now()
        apply_update_audit(level)

        if reason:
            level.notes = f"Cancelled: {reason}" if not level.notes else f"{level.notes}\nCancelled: {reason}"
        session.add(level)

        # Sync group's level_number if we cancelled the current active level
        group = session.get(Group, group_id)
        if group and group.level_number == level_number:
            # Find previous active level
            prev_active = repo.get_previous_active_level(session, group_id, level_number)
            if prev_active:
                group.level_number = prev_active.level_number
                session.add(group)

        self._uow.commit()
        self._uow.session.refresh(level)
        return level
