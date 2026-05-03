"""
app/modules/academics/repositories/group_history_repository.py
──────────────────────────────────────────────────────────────
Repository functions for Group History and Lifecycle tracking.
"""
from typing import Sequence
from sqlmodel import Session, select, func
from sqlalchemy import case
from datetime import datetime

from app.modules.academics.models.group_level_models import (
    GroupLevel,
    GroupCourseHistory,
    EnrollmentLevelHistory,
)
from app.modules.academics.models import Course
from app.modules.hr.models import Employee
from app.modules.crm.models.student_models import Student


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


# ════════════════════════════════════════════════════════════
# Group Analytics Repository Functions
# ════════════════════════════════════════════════════════════

def get_group_levels_with_details(
    session: Session, group_id: int
) -> Sequence[tuple[GroupLevel, str, str | None]]:
    """
    Get all group levels with course and instructor names.
    Returns tuples of (GroupLevel, course_name, instructor_name).
    """
    stmt = (
        select(GroupLevel)
        .where(GroupLevel.group_id == group_id)
        .order_by(GroupLevel.level_number.asc())
    )
    levels = session.exec(stmt).all()
    
    result = []
    for level in levels:
        # Get course name
        course = session.get(Course, level.course_id)
        course_name = course.name if course else "Unknown"
        
        # Get instructor name
        instructor_name = None
        if level.instructor_id:
            instructor = session.get(Employee, level.instructor_id)
            instructor_name = instructor.full_name if instructor else None
        
        result.append((level, course_name, instructor_name))
    
    return result


def get_level_student_counts(
    session: Session, group_id: int
) -> dict[int, int]: #TODO remove Dict and write a typed DTO class
    """
    Get student count per level for a group.
    Returns dict mapping level_number -> student_count.
    """
    # Count enrollments at each level based on EnrollmentLevelHistory
    stmt = (
        select(
            GroupLevel.level_number,
            func.count(func.distinct(EnrollmentLevelHistory.student_id)).label("student_count")
        )
        .join(EnrollmentLevelHistory, GroupLevel.id == EnrollmentLevelHistory.group_level_id)
        .where(GroupLevel.group_id == group_id)
        .group_by(GroupLevel.level_number)
    )
    
    results = session.exec(stmt).all()
    return {level_number: count for level_number, count in results}


def get_group_enrollments_with_details(
    session: Session,
    group_id: int,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100
) -> Sequence[tuple]:
    """
    Get enrollments for a group with student details.
    Returns tuples of (Enrollment, student_name, student_phone).
    """
    from app.modules.enrollments.models.enrollment_models import Enrollment
    
    stmt = (
        select(Enrollment, Student.full_name, Student.phone)
        .join(Student, Enrollment.student_id == Student.id)
        .where(Enrollment.group_id == group_id)
    )
    
    if status:
        stmt = stmt.where(Enrollment.status == status)
    
    stmt = stmt.order_by(Enrollment.enrolled_at.desc()).offset(skip).limit(limit)
    return session.exec(stmt).all()


def get_group_enrollment_stats(session: Session, group_id: int) -> dict: #TODO remove Dict and write a typed DTO class
    """
    Get enrollment statistics for a group.
    Returns: total, active, completed, dropped counts.
    """
    from app.modules.enrollments.models.enrollment_models import Enrollment
    
    stmt = (
        select(
            func.count().label("total"),
            func.sum(case((Enrollment.status == "active", 1), else_=0)).label("active"),
            func.sum(case((Enrollment.status == "completed", 1), else_=0)).label("completed"),
            func.sum(case((Enrollment.status == "dropped", 1), else_=0)).label("dropped"),
        )
        .where(Enrollment.group_id == group_id)
    )
    
    result = session.exec(stmt).first()
    return {
        "total": result[0] or 0,
        "active": result[1] or 0,
        "completed": result[2] or 0,
        "dropped": result[3] or 0,
    }


def get_enrollment_payments(session: Session, enrollment_id: int) -> float:
    """
    Get total payments made for an enrollment.
    """
    from app.modules.finance import Payment
    
    stmt = (
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.enrollment_id == enrollment_id)
        .where(Payment.transaction_type == "payment")
    )
    return session.exec(stmt).one() or 0.0


def get_group_instructors_summary(
    session: Session, group_id: int
) -> Sequence[tuple[int, str, datetime, datetime, int, bool]]: #TODO remove loose return types and write a typed DTO class
    """
    Get unique instructors for a group with summary stats.
    Returns: (instructor_id, instructor_name, first_assigned, last_assigned, levels_count, is_current)
    """
    # Get all levels with instructor info
    stmt = (
        select(GroupLevel)
        .where(GroupLevel.group_id == group_id)
        .where(GroupLevel.instructor_id.isnot(None))
        .order_by(GroupLevel.effective_from.asc())
    )
    levels = session.exec(stmt).all()
    
    # Group by instructor
    instructor_data: dict[int, dict] = {}
    current_instructor_id = None
    
    for level in levels:
        instructor_id = level.instructor_id
        if instructor_id is None:
            continue
            
        # Track current instructor (active level)
        if level.status == "active":
            current_instructor_id = instructor_id
        
        if instructor_id not in instructor_data:
            instructor = session.get(Employee, instructor_id)
            instructor_data[instructor_id] = {
                "name": instructor.full_name if instructor else "Unknown",
                "first_assigned": level.effective_from,
                "last_assigned": level.effective_from,
                "levels_count": 0,
            }
        
        data = instructor_data[instructor_id]
        if level.effective_from < data["first_assigned"]:
            data["first_assigned"] = level.effective_from
        if level.effective_from > data["last_assigned"]:
            data["last_assigned"] = level.effective_from
        data["levels_count"] += 1
    
    # Convert to result format
    result = []
    for instructor_id, data in instructor_data.items():
        result.append((
            instructor_id,
            data["name"],
            data["first_assigned"],
            data["last_assigned"],
            data["levels_count"],
            instructor_id == current_instructor_id
        ))
    
    return result


def get_group_competition_participations(
    session: Session, group_id: int
) -> Sequence[tuple]:
    """
    Get competition participation history for a group.
    Returns tuples with full participation details.
    """
    from app.modules.academics.models.group_level_models import GroupCompetitionParticipation
    from app.modules.competitions.models.competition_models import Competition
    from app.modules.competitions.models.team_models import Team
    
    stmt = (
        select(
            GroupCompetitionParticipation,
            Competition.name.label("competition_name"),
            Team.team_name,
            Team.category.label("category"),
            Team.subcategory.label("subcategory"),
        )
        .join(Competition, GroupCompetitionParticipation.competition_id == Competition.id)
        .join(Team, GroupCompetitionParticipation.team_id == Team.id)
        .where(GroupCompetitionParticipation.group_id == group_id)
        .order_by(GroupCompetitionParticipation.entered_at.desc())
    )
    return session.exec(stmt).all()
