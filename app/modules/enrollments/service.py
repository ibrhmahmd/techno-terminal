from datetime import date, datetime, timezone
from app.db.connection import get_session
from app.modules.crm.repository import get_student_by_id
from app.modules.academics.repository import list_groups_by_course
from sqlmodel import Session, select
from app.modules.academics.models import Group
from app.modules.crm.models import Student
from .models import Enrollment
from . import repository as repo


def _get_group(session: Session, group_id: int) -> Group | None:
    return session.get(Group, group_id)


def _get_student(session: Session, student_id: int) -> Student | None:
    return session.get(Student, student_id)


def enroll_student(
    student_id: int,
    group_id: int,
    amount_due: float | None = None,
    discount: float = 0.0,
    notes: str | None = None,
    created_by: int | None = None,
) -> tuple[Enrollment, bool]:
    """
    Enrolls a student in a group.
    Returns (enrollment, capacity_exceeded: bool).
    capacity_exceeded=True means the group is over the soft limit — admin chose to proceed.
    Raises ValueError for hard failures (student inactive, group inactive, already enrolled).
    """
    with get_session() as session:
        # 1. Validate student
        student = _get_student(session, student_id)
        if not student:
            raise ValueError(f"Student ID {student_id} not found.")
        if not student.is_active:
            raise ValueError(f"Student '{student.full_name}' is not active.")

        # 2. Validate group
        group = _get_group(session, group_id)
        if not group:
            raise ValueError(f"Group ID {group_id} not found.")
        if group.status != "active":
            raise ValueError(
                f"Group '{group.name}' is not active (status: {group.status})."
            )

        # 3. Duplicate check
        existing = repo.get_active_enrollment(session, student_id, group_id)
        if existing:
            raise ValueError(
                f"'{student.full_name}' is already enrolled in this group (Enrollment ID: {existing.id})."
            )

        # 4. Soft capacity check
        active_enrollments = repo.list_enrollments(
            session, group_id=group_id, status="active"
        )
        capacity_exceeded = (
            group.max_capacity is not None
            and len(active_enrollments) >= group.max_capacity
        )

        # 5. Create enrollment — snapshot level from group
        enrollment = Enrollment(
            student_id=student_id,
            group_id=group_id,
            level_number=group.level_number,  # Snapshot
            enrolled_at=datetime.now(timezone.utc),
            amount_due=amount_due,
            discount_applied=discount,
            notes=notes,
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
        )

        created = repo.create_enrollment(session, enrollment)
        return created, capacity_exceeded


def apply_sibling_discount(
    enrollment_id: int, discount_amount: float = 50.0
) -> Enrollment:
    """Applies the sibling discount to an existing active enrollment."""
    with get_session() as session:
        enrollment = repo.get_enrollment(session, enrollment_id)
        if not enrollment:
            raise ValueError(f"Enrollment {enrollment_id} not found.")
        if enrollment.status != "active":
            raise ValueError("Can only apply discount to active enrollments.")
        updated = repo.update_discount(session, enrollment_id, discount_amount)
        return updated


def transfer_student(
    from_enrollment_id: int, to_group_id: int, created_by: int | None = None
) -> Enrollment:
    """Marks the old enrollment as 'transferred' and creates a new one in the target group."""
    with get_session() as session:
        source = repo.get_enrollment(session, from_enrollment_id)
        if not source:
            raise ValueError(f"Source enrollment {from_enrollment_id} not found.")
        if source.status != "active":
            raise ValueError("Can only transfer an active enrollment.")

        target_group = _get_group(session, to_group_id)
        if not target_group:
            raise ValueError(f"Target group {to_group_id} not found.")
        if target_group.status != "active":
            raise ValueError(f"Target group '{target_group.name}' is not active.")

        # Mark source as transferred
        repo.update_enrollment_status(session, from_enrollment_id, "transferred")

        # Create new enrollment
        new_enrollment = Enrollment(
            student_id=source.student_id,
            group_id=to_group_id,
            level_number=target_group.level_number,
            enrolled_at=datetime.now(timezone.utc),
            amount_due=source.amount_due,
            discount_applied=source.discount_applied,
            transferred_from=from_enrollment_id,
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
        )
        return repo.create_enrollment(session, new_enrollment)


def drop_enrollment(enrollment_id: int) -> Enrollment:
    with get_session() as session:
        enrollment = repo.get_enrollment(session, enrollment_id)
        if not enrollment:
            raise ValueError(f"Enrollment {enrollment_id} not found.")
        return repo.update_enrollment_status(session, enrollment_id, "dropped")


def complete_enrollment(enrollment_id: int) -> Enrollment:
    with get_session() as session:
        enrollment = repo.get_enrollment(session, enrollment_id)
        if not enrollment:
            raise ValueError(f"Enrollment {enrollment_id} not found.")
        return repo.update_enrollment_status(session, enrollment_id, "completed")


def get_group_roster(
    group_id: int, level_number: int | None = None
) -> list[Enrollment]:
    """Returns all active enrollments for a group (optionally filtered by level)."""
    with get_session() as session:
        return list(
            repo.list_enrollments(
                session, group_id=group_id, level_number=level_number, status="active"
            )
        )


def get_student_enrollments(student_id: int) -> list[Enrollment]:
    """Returns all enrollments for a student across all groups."""
    with get_session() as session:
        stmt = select(Enrollment).where(Enrollment.student_id == student_id)
        return list(session.exec(stmt).all())
