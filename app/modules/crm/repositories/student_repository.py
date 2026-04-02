from typing import Sequence
from sqlmodel import Session, select
from app.modules.crm.models import Student, StudentParent
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
