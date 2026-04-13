from typing import Optional, Sequence
from sqlmodel import Session, select, delete, func
from datetime import datetime
import json

from app.modules.crm.models import Student, StudentParent, StudentStatus, Parent
from app.shared.audit_utils import apply_create_audit

def create_student(session: Session, student: Student) -> Student:
    session.add(student)
    session.flush()
    return student

def get_student_by_id(session: Session, student_id: int) -> Student | None:
    return session.get(Student, student_id)

def get_all_students(session: Session, skip: int = 0, limit: int = 200) -> Sequence[Student]:
    stmt = select(Student).offset(skip).limit(limit)
    return session.exec(stmt).all()

def search_students(session: Session, query: str) -> Sequence[Student]:
    search_term = f"%{query}%"
    stmt = select(Student).where(Student.full_name.ilike(search_term)).limit(50)
    return session.exec(stmt).all()

def get_student_parents(session: Session, student_id: int) -> Sequence[StudentParent]:
    """Retrieves the parent link objects for a given student."""
    stmt = select(StudentParent).where(StudentParent.student_id == student_id)
    return session.exec(stmt).all()

def link_parent(
    session: Session,
    student_id: int,
    parent_id: int,
    relationship: str | None = None,
    is_primary: bool = False,
) -> StudentParent:
    link = StudentParent(
        student_id=student_id,
        parent_id=parent_id,
        relationship=relationship,
        is_primary=is_primary,
    )
    apply_create_audit(link)
    session.add(link)
    session.flush()
    return link

def get_siblings(session: Session, student_id: int) -> list[dict]:
    """
    Returns sibling data via ORM joins on StudentParent.
    Two-query approach: find shared parents, then find their other students.
    """
    parent_links = session.exec(
        select(StudentParent).where(StudentParent.student_id == student_id)
    ).all()
    parent_ids = [link.parent_id for link in parent_links]
    if not parent_ids:
        return []

    sibling_links = session.exec(
        select(StudentParent)
        .where(StudentParent.parent_id.in_(parent_ids))
        .where(StudentParent.student_id != student_id)
    ).all()
    sibling_ids = {link.student_id for link in sibling_links}

    return [
        {"sibling_id": s.id, "sibling_name": s.full_name}
        for sid in sibling_ids
        if (s := session.get(Student, sid))
    ]

def get_students_by_parent_id(
    session: Session, parent_id: int, active_only: bool = True
) -> list[Student]:
    """
    Returns all Student objects linked to a parent via StudentParent.
    Single JOIN — avoids N+1 query anti-pattern.
    """
    stmt = (
        select(Student)
        .join(StudentParent, StudentParent.student_id == Student.id)
        .where(StudentParent.parent_id == parent_id)
    )
    if active_only:
        stmt = stmt.where(Student.is_active)
    return list(session.exec(stmt).all())


def count_students(session: Session, active_only: bool = True) -> int:
    """Returns total count of students for pagination."""
    stmt = select(Student)
    if active_only:
        stmt = stmt.where(Student.is_active.is_(True))
    return len(session.exec(stmt).all())


# ── NEW: Waiting List and Status Management Methods ────────────────────────────

def get_students_by_status(
    session: Session,
    status: StudentStatus,
    skip: int = 0,
    limit: int = 200
) -> Sequence[Student]:
    """Retrieve students by their enrollment status."""
    stmt = (
        select(Student)
        .where(Student.status == status)
        .offset(skip)
        .limit(limit)
    )
    return session.exec(stmt).all()


def get_waiting_list(
    session: Session,
    skip: int = 0,
    limit: int = 200,
    order_by_priority: bool = True
) -> Sequence[Student]:
    """Retrieve students on waiting list, ordered by priority and date."""
    stmt = select(Student).where(Student.status == StudentStatus.WAITING)
    if order_by_priority:
        stmt = stmt.order_by(
            Student.waiting_priority.asc().nullslast(),
            Student.waiting_since.asc()
        )
    else:
        stmt = stmt.order_by(Student.waiting_since.asc())
    return session.exec(stmt.offset(skip).limit(limit)).all()


def count_students_by_status(session: Session, status: Optional[StudentStatus] = None) -> int:
    """Count students by status. If no status provided, count all."""
    stmt = select(Student)
    if status:
        stmt = stmt.where(Student.status == status)
    return len(session.exec(stmt).all())


def update_student_status(
    session: Session,
    student_id: int,
    new_status: StudentStatus,
    user_id: Optional[int] = None,
    notes: Optional[str] = None
) -> Student | None:
    """Update student status with audit logging."""
    student = get_student_by_id(session, student_id)
    if not student:
        return None
    
    old_status = student.status
    
    # Helper to extract value from either enum or string (DB returns strings)
    def _get_status_value(status):
        if status is None:
            return None
        return status.value if hasattr(status, 'value') else str(status)
    
    # Create audit entry
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "changed_by": user_id,
        "old_status": _get_status_value(old_status),
        "new_status": _get_status_value(new_status),
        "notes": notes
    }
    
    # Update status_history in JSONB
    history = student.status_history or []
    if isinstance(history, str):
        history = json.loads(history) if history else []
    history.append(audit_entry)
    student.status_history = history
    
    # Update status and trigger will handle waiting_since
    student.status = new_status
    student.is_active = new_status in [StudentStatus.ACTIVE, StudentStatus.WAITING]
    
    if notes:
        student.waiting_notes = notes
    
    session.add(student)
    session.flush()
    return student


def set_waiting_priority(
    session: Session,
    student_id: int,
    priority: int
) -> Student | None:
    """Set priority for a student on the waiting list."""
    student = get_student_by_id(session, student_id)
    if not student or student.status != StudentStatus.WAITING:
        return None
    
    student.waiting_priority = priority
    session.add(student)
    session.flush()
    return student


def search_students_with_filters(
    session: Session,
    query: str,
    status: Optional[StudentStatus] = None,
    limit: int = 50
) -> Sequence[Student]:
    """Search students by name with optional status filter."""
    search_term = f"%{query}%"
    stmt = select(Student).where(Student.full_name.ilike(search_term))
    if status:
        stmt = stmt.where(Student.status == status)
    return session.exec(stmt.limit(limit)).all()


def delete_student_by_id(
    session: Session,
    student_id: int,
) -> bool:
    """Delete a student by ID."""
    # Local imports to avoid circular dependency
    from app.modules.enrollments.models.enrollment_models import Enrollment
    from app.modules.attendance.models.attendance_models import Attendance
    from app.modules.finance.finance_models import Payment
    
    student = get_student_by_id(session, student_id)
    if not student:
        return False
    
    # Get enrollment IDs for this student
    enrollment_stmt = select(Enrollment.id).where(Enrollment.student_id == student_id)
    enrollment_ids = list(session.scalars(enrollment_stmt))
    
    # Delete attendance records for these enrollments first
    if enrollment_ids:
        attendance_stmt = delete(Attendance).where(Attendance.enrollment_id.in_(enrollment_ids))
        session.exec(attendance_stmt)
        
        # Delete payments for these enrollments
        payments_stmt = delete(Payment).where(Payment.enrollment_id.in_(enrollment_ids))
        session.exec(payments_stmt)
    
    # Delete related enrollments (FK constraint)
    stmt = delete(Enrollment).where(Enrollment.student_id == student_id)
    session.exec(stmt)
    
    session.delete(student)
    session.flush()
    return True


# ── NEW: Student Detail Query Methods ─────────────────────────────────────────

def get_student_with_parent(
    session: Session,
    student_id: int
) -> tuple[Student, Optional["Parent"]] | None:
    """
    Get student with their primary parent (if linked).
    Returns tuple of (student, parent) or None if student not found.
    """
    # Get student
    student = get_student_by_id(session, student_id)
    if not student:
        return None
    
    # Get primary parent link
    primary_link = session.exec(
        select(StudentParent)
        .where(StudentParent.student_id == student_id)
        .where(StudentParent.is_primary.is_(True))
    ).first()
    
    if primary_link and primary_link.parent_id:
        from app.modules.crm.models.parent_models import Parent
        parent = session.get(Parent, primary_link.parent_id)
    else:
        parent = None
    
    return (student, parent)


def get_student_enrollments_with_details(
    session: Session,
    student_id: int
) -> "list[EnrollmentInfo]":
    """
    Get student's active enrollments with group and course details.
    Returns list of EnrollmentInfo DTOs.
    """
    from app.modules.enrollments.models.enrollment_models import Enrollment
    from app.modules.academics.models.group_models import Group
    from app.modules.academics.models.course_models import Course
    from app.api.schemas.crm.student_details import EnrollmentInfo
    
    stmt = (
        select(Enrollment, Group, Course)
        .join(Group, Enrollment.group_id == Group.id)
        .join(Course, Group.course_id == Course.id)
        .where(Enrollment.student_id == student_id)
        .where(Enrollment.status.in_(['active', 'completed']))
        .order_by(Enrollment.enrolled_at.desc())
    )
    
    results = session.exec(stmt).all()
    enrollments_data: list[EnrollmentInfo] = []
    
    for enrollment, group, course in results:
        enrollments_data.append(EnrollmentInfo(
            enrollment_id=enrollment.id,
            group_id=group.id,
            group_name=group.group_name,
            course_id=course.id,
            course_name=course.name,
            level_number=enrollment.level_number,
            status=enrollment.status,
            amount_due=float(enrollment.amount_due) if enrollment.amount_due else None,
            discount_applied=float(enrollment.discount_applied or 0),
            enrolled_at=enrollment.enrolled_at,
        ))
    
    return enrollments_data


def get_student_balance_summary(
    session: Session,
    student_id: int
) -> "StudentBalanceSummary":
    """
    Calculate balance summary for a student.
    Returns StudentBalanceSummary DTO.
    """
    from decimal import Decimal
    from app.modules.enrollments.models.enrollment_models import Enrollment
    from app.modules.finance.models.balance_models import PaymentAllocation
    from app.modules.finance.finance_models import Payment
    from app.api.schemas.crm.student_details import StudentBalanceSummary
    
    # Get active/completed enrollments
    enrollments = session.exec(
        select(Enrollment)
        .where(Enrollment.student_id == student_id)
        .where(Enrollment.status.in_(['active', 'completed']))
    ).all()
    
    total_due = Decimal('0.00')
    total_discounts = Decimal('0.00')
    total_paid = Decimal('0.00')
    unpaid_count = 0
    
    for enrollment in enrollments:
        due = Decimal(str(enrollment.amount_due or 0))
        discount = Decimal(str(enrollment.discount_applied or 0))
        
        # Get payments for this enrollment
        allocations = session.exec(
            select(PaymentAllocation)
            .join(Payment, PaymentAllocation.payment_id == Payment.id)
            .where(PaymentAllocation.enrollment_id == enrollment.id)
            .where(Payment.transaction_type == 'payment')
        ).all()
        
        paid = sum(Decimal(str(alloc.allocated_amount)) for alloc in allocations)
        
        total_due += due
        total_discounts += discount
        total_paid += paid
        
        # Count as unpaid if remaining > 0
        remaining = due - discount - paid
        if remaining > 0:
            unpaid_count += 1
    
    net_balance = float(total_paid - (total_due - total_discounts))
    
    return StudentBalanceSummary(
        total_due=float(total_due),
        total_discounts=float(total_discounts),
        total_paid=float(total_paid),
        net_balance=net_balance,
        enrollment_count=len(enrollments),
        unpaid_enrollments=unpaid_count,
    )


def get_student_siblings_with_details(
    session: Session,
    student_id: int
) -> "list['SiblingInfo']" :
    """
    Get siblings with detailed information including parent name and enrollment count.
    Returns list of SiblingInfo DTOs.
    """
    from datetime import datetime
    from app.modules.enrollments.models.enrollment_models import Enrollment
    from app.api.schemas.crm.student_details import SiblingInfo
    
    # Get student's parent links
    parent_links = session.exec(
        select(StudentParent).where(StudentParent.student_id == student_id)
    ).all()
    
    if not parent_links:
        return []
    
    parent_ids = [link.parent_id for link in parent_links]
    
    # Get siblings (students sharing any of these parents)
    sibling_links = session.exec(
        select(StudentParent, Student, Parent)
        .join(Student, StudentParent.student_id == Student.id)
        .join(Parent, StudentParent.parent_id == Parent.id)
        .where(StudentParent.parent_id.in_(parent_ids))
        .where(StudentParent.student_id != student_id)
    ).all()
    
    # Deduplicate siblings (could be linked through multiple parents)
    seen_ids = set()
    siblings_data = []
    
    for link, sibling, parent in sibling_links:
        if sibling.id in seen_ids:
            continue
        seen_ids.add(sibling.id)
        
        # Calculate age
        age = None
        if sibling.date_of_birth:
            today = datetime.now()
            age = today.year - sibling.date_of_birth.year
            if (today.month, today.day) < (sibling.date_of_birth.month, sibling.date_of_birth.day):
                age -= 1
        
        # Count active enrollments
        enrollment_count = session.exec(
            select(func.count(Enrollment.id))
            .where(Enrollment.student_id == sibling.id)
            .where(Enrollment.status == 'active')
        ).one()
        
        siblings_data.append(SiblingInfo(
            student_id=sibling.id,
            full_name=sibling.full_name,
            age=age,
            gender=sibling.gender,
            status=str(sibling.status) if sibling.status else "active",
            parent_id=parent.id,
            parent_name=parent.full_name,
            enrollments_count=enrollment_count,
        ))
    
    return siblings_data