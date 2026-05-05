"""
app/modules/academics/repositories/group_history_repository.py
──────────────────────────────────────────────────────────────
Repository functions for Group History and Lifecycle tracking.
"""
from datetime import datetime
from typing import Sequence, Optional
from sqlmodel import Session, select, func
from sqlalchemy import case
from app.shared.datetime_utils import utc_now

from app.modules.academics.models.group_level_models import (
    GroupLevel,
    GroupCourseHistory,
    EnrollmentLevelHistory,
)
from app.modules.academics.models import Course
from app.modules.hr.models import Employee
from app.modules.crm.models.student_models import Student
from app.modules.academics.constants import (
    LEVEL_STATUS_ACTIVE, LEVEL_STATUS_COMPLETED,
    ENROLLMENT_STATUS_ACTIVE, ENROLLMENT_STATUS_COMPLETED, ENROLLMENT_STATUS_DROPPED,
    TRANSACTION_TYPE_PAYMENT,
)
from app.modules.academics.group.details.schemas import EnrollmentStatsDTO, PaymentStatsDTO


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
        assigned_at=utc_now(),
        assigned_by_user_id=assigned_by_user_id,
        notes=notes,
    )
    from app.shared.audit_utils import apply_create_audit
    apply_create_audit(history)
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
        record.removed_at = utc_now()
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
        level_entered_at=utc_now(),
        status=LEVEL_STATUS_ACTIVE,
    )
    from app.shared.audit_utils import apply_create_audit
    apply_create_audit(transition)
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
        record.level_completed_at = utc_now()
        record.status = LEVEL_STATUS_COMPLETED
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
            func.sum(case((Enrollment.status == ENROLLMENT_STATUS_ACTIVE, 1), else_=0)).label("active"),
            func.sum(case((Enrollment.status == ENROLLMENT_STATUS_COMPLETED, 1), else_=0)).label("completed"),
            func.sum(case((Enrollment.status == ENROLLMENT_STATUS_DROPPED, 1), else_=0)).label("dropped"),
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
        .where(Payment.transaction_type == TRANSACTION_TYPE_PAYMENT)
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
        if level.status == LEVEL_STATUS_ACTIVE:
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


def get_enrollment_stats_by_levels(
    session: Session, group_id: int, level_numbers: list[int]
) -> dict[int, EnrollmentStatsDTO]:
    """Get enrollment counts per level."""
    from app.modules.enrollments.models.enrollment_models import Enrollment

    stmt = (
        select(
            Enrollment.level_number,
            Enrollment.status,
            func.count().label("count")
        )
        .where(Enrollment.group_id == group_id)
        .where(Enrollment.level_number.in_(level_numbers))
        .group_by(Enrollment.level_number, Enrollment.status)
    )
    results = session.exec(stmt).all()

    # Aggregate per level
    stats: dict[int, EnrollmentStatsDTO] = {
        ln: EnrollmentStatsDTO() for ln in level_numbers
    }
    for row in results:
        ln = row.level_number
        status = row.status
        count = row.count
        stats[ln].total += count
        if status == ENROLLMENT_STATUS_COMPLETED:
            stats[ln].completed += count
        elif status == ENROLLMENT_STATUS_DROPPED:
            stats[ln].dropped += count

    return stats


def get_payment_stats_by_levels(
    session: Session, group_id: int, level_numbers: list[int]
) -> dict[int, PaymentStatsDTO]:
    """Get payment aggregates per level using enrollment data."""
    from app.modules.enrollments.models.enrollment_models import Enrollment
    from app.modules.finance.models.payment import Payment

    # Get enrollments with their payment status per level
    stmt = (
        select(
            Enrollment.level_number,
            Enrollment.amount_due,
            Enrollment.discount_applied,
            func.coalesce(
                func.sum(Payment.amount),
                0
            ).label("total_paid")
        )
        .outerjoin(
            Payment,
            (Payment.enrollment_id == Enrollment.id) &
            (Payment.deleted_at.is_(None))
        )
        .where(Enrollment.group_id == group_id)
        .where(Enrollment.level_number.in_(level_numbers))
        .where(Enrollment.status.in_([ENROLLMENT_STATUS_ACTIVE, ENROLLMENT_STATUS_COMPLETED]))
        .group_by(Enrollment.id, Enrollment.level_number, Enrollment.amount_due, Enrollment.discount_applied)
    )
    results = session.exec(stmt).all()

    # Aggregate per level
    stats: dict[int, PaymentStatsDTO] = {
        ln: PaymentStatsDTO() for ln in level_numbers
    }

    for row in results:
        ln = row.level_number
        amount_due = float(row.amount_due or 0)
        discount = float(row.discount_applied or 0)
        total_paid = float(row.total_paid or 0)

        expected = amount_due - discount
        due = expected - total_paid

        stats[ln].expected += expected
        stats[ln].collected += total_paid
        stats[ln].due += max(0, due)
        if due > 0:
            stats[ln].unpaid_count += 1

    return stats
