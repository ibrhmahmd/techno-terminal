from datetime import date
from sqlalchemy.exc import IntegrityError
from app.db.connection import get_session
from app.shared.audit_utils import apply_create_audit
from app.shared.datetime_utils import utc_now
from app.modules.crm import crm_service as crm_srv
from app.modules.academics import academics_service as acad_srv
from app.modules.enrollments.enrollment_models import Enrollment
from app.shared.exceptions import NotFoundError, BusinessRuleError, ConflictError
from . import enrollment_repository as repo


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
    Cross-module validation is done via service calls (each opens its own read session).
    Enrollment data is written in a separate session.
    """
    # 1. Validate student — via CRM service (no shared session)
    student = crm_srv.get_student_by_id(student_id)
    if not student:
        raise NotFoundError(f"Student ID {student_id} not found.")
    if not student.is_active:
        raise BusinessRuleError(f"Student '{student.full_name}' is not active.")

    # 2. Validate group — via Academics service (no shared session)
    group = acad_srv.get_group_by_id(group_id)
    if not group:
        raise NotFoundError(f"Group ID {group_id} not found.")
    if group.status != "active":
        raise BusinessRuleError(
            f"Group '{group.name}' is not active (status: {group.status})."
        )

    # 3. Enrollment-specific logic in its own session
    try:
        with get_session() as session:
            # Duplicate check (application-level fast path)
            existing = repo.get_active_enrollment(session, student_id, group_id)
            if existing:
                raise ConflictError(
                    f"'{student.full_name}' is already enrolled in this group (Enrollment ID: {existing.id})."
                )

            # Soft capacity check
            active_enrollments = repo.list_enrollments(
                session, group_id=group_id, status="active"
            )
            capacity_exceeded = (
                group.max_capacity is not None
                and len(active_enrollments) >= group.max_capacity
            )

            # Create enrollment — snapshot level from group
            enrollment = Enrollment(
                student_id=student_id,
                group_id=group_id,
                level_number=group.level_number,  # Snapshot at enrollment time
                enrolled_at=utc_now(),
                amount_due=amount_due,
                discount_applied=discount,
                notes=notes,
                created_by=created_by,
                created_at=utc_now(),
            )
            created = repo.create_enrollment(session, enrollment)
            return created, capacity_exceeded
    except IntegrityError:
        # The partial unique index on (student_id, group_id) WHERE status='active'
        # caught a race condition — another request committed first.
        # Requires: CREATE UNIQUE INDEX uq_enrollment_active
        #           ON enrollments (student_id, group_id) WHERE status = 'active';
        raise ConflictError(
            f"'{student.full_name}' was just enrolled in this group by another request. "
            "Please refresh and try again."
        )


def apply_sibling_discount(
    enrollment_id: int, discount_amount: float = 50.0
) -> Enrollment:
    """Applies the sibling discount to an existing active enrollment."""
    with get_session() as session:
        enrollment = repo.get_enrollment(session, enrollment_id)
        if not enrollment:
            raise NotFoundError(f"Enrollment {enrollment_id} not found.")
        if enrollment.status != "active":
            raise BusinessRuleError("Can only apply discount to active enrollments.")
        updated = repo.update_discount(session, enrollment_id, discount_amount)
        return updated


def transfer_student(
    from_enrollment_id: int, to_group_id: int, created_by: int | None = None
) -> Enrollment:
    """Marks the old enrollment as 'transferred' and creates a new one in the target group."""
    # Validate target group via Academics service first
    target_group = acad_srv.get_group_by_id(to_group_id)
    if not target_group:
        raise NotFoundError(f"Target group {to_group_id} not found.")
    if target_group.status != "active":
        raise BusinessRuleError(f"Target group '{target_group.name}' is not active.")

    with get_session() as session:
        source = repo.get_enrollment(session, from_enrollment_id)
        if not source:
            raise NotFoundError(f"Source enrollment {from_enrollment_id} not found.")
        if source.status != "active":
            raise BusinessRuleError("Can only transfer an active enrollment.")

        # Mark source as transferred
        repo.update_enrollment_status(session, from_enrollment_id, "transferred")

        # Create new enrollment in target group
        new_enrollment = Enrollment(
            student_id=source.student_id,
            group_id=to_group_id,
            level_number=target_group.level_number,
            enrolled_at=utc_now(),
            amount_due=source.amount_due,
            discount_applied=source.discount_applied,
            transferred_from=from_enrollment_id,
            created_by=created_by,
        )
        apply_create_audit(new_enrollment)
        return repo.create_enrollment(session, new_enrollment)


def drop_enrollment(enrollment_id: int) -> Enrollment:
    with get_session() as session:
        enrollment = repo.get_enrollment(session, enrollment_id)
        if not enrollment:
            raise NotFoundError(f"Enrollment {enrollment_id} not found.")
        return repo.update_enrollment_status(session, enrollment_id, "dropped")


def complete_enrollment(enrollment_id: int) -> Enrollment:
    with get_session() as session:
        enrollment = repo.get_enrollment(session, enrollment_id)
        if not enrollment:
            raise NotFoundError(f"Enrollment {enrollment_id} not found.")
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
        return repo.get_enrollments_by_student(session, student_id)
