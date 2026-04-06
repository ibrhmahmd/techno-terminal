from typing import Optional, Sequence
from sqlmodel import Session, select
from datetime import datetime
import json

from app.modules.crm.models import Student, StudentParent, StudentStatus
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
        stmt = stmt.where(Student.is_active == True)
    return list(session.exec(stmt).all())


def count_students(session: Session, active_only: bool = True) -> int:
    """Returns total count of students for pagination."""
    stmt = select(Student)
    if active_only:
        stmt = stmt.where(Student.is_active == True)
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
    
    # Create audit entry
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "changed_by": user_id,
        "old_status": old_status.value if old_status else None,
        "new_status": new_status.value,
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
