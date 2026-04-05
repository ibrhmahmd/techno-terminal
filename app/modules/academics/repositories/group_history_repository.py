"""
app/modules/academics/repositories/group_history_repository.py
──────────────────────────────────────────────────────────────
Repository functions for Group History and Lifecycle tracking.
"""
from typing import Sequence
from sqlmodel import Session, select, func
from datetime import datetime

from app.modules.academics.models.group_level_models import (
    GroupLevel,
    GroupCourseHistory,
    EnrollmentLevelHistory,
)
from app.modules.academics.models import Group, Course
from app.modules.hr.hr_models import Employee
from app.modules.crm.models.student_models import Student


def get_group_levels_timeline(
    session: Session, group_id: int
) -> Sequence[GroupLevel]:
    """Get chronological timeline of all level snapshots for a group."""
    stmt = (
        select(GroupLevel)
        .where(GroupLevel.group_id == group_id)
        .order_by(GroupLevel.level_number.asc())
    )
    return session.exec(stmt).all()


def get_group_course_assignments(
    session: Session, group_id: int
) -> Sequence[GroupCourseHistory]:
    """Get chronological course assignment history for a group."""
    stmt = (
        select(GroupCourseHistory)
        .where(GroupCourseHistory.group_id == group_id)
        .order_by(GroupCourseHistory.assigned_at.asc())
    )
    return session.exec(stmt).all()


def record_course_assignment(
    session: Session,
    group_id: int,
    course_id: int,
    assigned_by_user_id: int | None = None,
    notes: str | None = None,
) -> GroupCourseHistory:
    """Record a new course assignment."""
    history = GroupCourseHistory(
        group_id=group_id,
        course_id=course_id,
        assigned_at=datetime.utcnow(),
        assigned_by_user_id=assigned_by_user_id,
        notes=notes,
    )
    session.add(history)
    session.flush()
    return history


def complete_course_assignment(
    session: Session, group_id: int, course_id: int
) -> GroupCourseHistory | None:
    """Mark a course assignment as completed/removed."""
    stmt = (
        select(GroupCourseHistory)
        .where(GroupCourseHistory.group_id == group_id)
        .where(GroupCourseHistory.course_id == course_id)
        .where(GroupCourseHistory.removed_at.is_(None))
    )
    record = session.exec(stmt).first()
    if record:
        record.removed_at = datetime.utcnow()
        session.add(record)
        session.flush()
    return record


def get_enrollment_transitions(
    session: Session, group_id: int, student_id: int | None = None
) -> Sequence[EnrollmentLevelHistory]:
    """Get level transition history for enrollments in a group."""
    stmt = select(EnrollmentLevelHistory).where(
        EnrollmentLevelHistory.group_level_id.in_(
            select(GroupLevel.id).where(GroupLevel.group_id == group_id)
        )
    )
    if student_id:
        stmt = stmt.where(EnrollmentLevelHistory.student_id == student_id)
    stmt = stmt.order_by(EnrollmentLevelHistory.level_entered_at.asc())
    return session.exec(stmt).all()


def record_enrollment_level_transition(
    session: Session,
    enrollment_id: int,
    group_level_id: int,
    student_id: int,
) -> EnrollmentLevelHistory:
    """Record when a student enters a new level."""
    transition = EnrollmentLevelHistory(
        enrollment_id=enrollment_id,
        group_level_id=group_level_id,
        student_id=student_id,
        level_entered_at=datetime.utcnow(),
        status="active",
    )
    session.add(transition)
    session.flush()
    return transition


def complete_enrollment_level(
    session: Session, enrollment_id: int, group_level_id: int
) -> EnrollmentLevelHistory | None:
    """Mark an enrollment level as completed."""
    stmt = (
        select(EnrollmentLevelHistory)
        .where(EnrollmentLevelHistory.enrollment_id == enrollment_id)
        .where(EnrollmentLevelHistory.group_level_id == group_level_id)
        .where(EnrollmentLevelHistory.level_completed_at.is_(None))
    )
    record = session.exec(stmt).first()
    if record:
        record.level_completed_at = datetime.utcnow()
        record.status = "completed"
        session.add(record)
        session.flush()
    return record


def get_full_group_lifecycle(session: Session, group_id: int) -> dict:
    """Get complete lifecycle data for a group (levels + courses + stats)."""
    group = session.get(Group, group_id)
    if not group:
        return {}
    
    levels = get_group_levels_timeline(session, group_id)
    courses = get_group_course_assignments(session, group_id)
    
    # Calculate stats
    total_levels = len(levels)
    completed_levels = sum(1 for l in levels if l.status == "completed")
    
    return {
        "group_id": group_id,
        "group_name": group.name,
        "created_at": group.created_at,
        "current_level": group.level_number,
        "total_levels": total_levels,
        "completed_levels": completed_levels,
        "levels_timeline": levels,
        "course_assignments": courses,
    }
