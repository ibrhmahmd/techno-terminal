"""
app/modules/academics/repositories/group_history_repository.py
──────────────────────────────────────────────────────────────
Repository functions for Group History and Lifecycle tracking.
"""
from sqlmodel import Session, select, func
from sqlalchemy import case

from app.modules.academics.models.group_level_models import (
    GroupLevel,
)
from app.modules.hr.models import Employee
from app.modules.crm.models.student_models import Student
from app.modules.academics.constants import (
    LEVEL_STATUS_ACTIVE, ENROLLMENT_STATUS_ACTIVE, ENROLLMENT_STATUS_COMPLETED, ENROLLMENT_STATUS_DROPPED,
    TRANSACTION_TYPE_PAYMENT,
)
from app.modules.academics.schemas.group_details_schemas import EnrollmentStatsDTO, PaymentStatsDTO
from app.modules.academics.schemas.group_analytics_schemas import (
    GroupEnrollmentStatsDTO,
    GroupEnrollmentDetailDTO,
    GroupInstructorSummaryDTO,
)
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.finance.models.payment import Payment


# ════════════════════════════════════════════════════════════
# Group Analytics Repository Functions
# ════════════════════════════════════════════════════════════



def get_group_enrollments_with_details(
    session: Session,
    group_id: int,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100
) -> list[GroupEnrollmentDetailDTO]:
    """
    Get enrollments for a group with student details.
    Returns GroupEnrollmentDetailDTO rows.
    """
    stmt = (
        select(Enrollment, Student.full_name, Student.phone)
        .join(Student, Enrollment.student_id == Student.id)
        .where(Enrollment.group_id == group_id)
    )
    
    if status:
        stmt = stmt.where(Enrollment.status == status)
    
    stmt = stmt.order_by(Enrollment.enrolled_at.desc()).offset(skip).limit(limit)
    rows = session.exec(stmt).all()
    return [
        GroupEnrollmentDetailDTO(
            enrollment_id=enrollment.id,
            student_id=enrollment.student_id,
            student_name=student_name,
            student_phone=student_phone,
            level_number=enrollment.level_number,
            enrolled_at=enrollment.enrolled_at,
            status=enrollment.status,
            amount_due=enrollment.amount_due or 0.0,
            discount_applied=enrollment.discount_applied or 0.0,
        )
        for enrollment, student_name, student_phone in rows
    ]


def get_group_enrollment_stats(session: Session, group_id: int) -> GroupEnrollmentStatsDTO:
    """
    Get enrollment statistics for a group.
    Returns: total, active, completed, dropped counts.
    """
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
    return GroupEnrollmentStatsDTO(
        total=result[0] or 0,
        active=result[1] or 0,
        completed=result[2] or 0,
        dropped=result[3] or 0,
    )


def get_enrollment_payments(session: Session, enrollment_id: int) -> float:
    """
    Get total payments made for an enrollment.
    """
    stmt = (
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.enrollment_id == enrollment_id)
        .where(Payment.transaction_type == TRANSACTION_TYPE_PAYMENT)
    )
    return session.exec(stmt).one() or 0.0


def get_group_instructors_summary(
    session: Session, group_id: int
) -> list[GroupInstructorSummaryDTO]:
    """
    Get unique instructors for a group with summary stats.
    Returns GroupInstructorSummaryDTO rows.
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
        result.append(GroupInstructorSummaryDTO(
            instructor_id=instructor_id,
            instructor_name=data["name"],
            first_assigned=data["first_assigned"],
            last_assigned=data["last_assigned"],
            levels_count=data["levels_count"],
            is_current=instructor_id == current_instructor_id,
        ))
    
    return result


def get_enrollment_stats_by_levels(
    session: Session, group_id: int, level_numbers: list[int]
) -> dict[int, EnrollmentStatsDTO]:
    """Get enrollment counts per level."""
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
