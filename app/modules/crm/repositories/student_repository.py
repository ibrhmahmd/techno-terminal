from typing import Sequence
from sqlmodel import Session, select
from app.modules.crm.models import Student, StudentGuardian
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

def get_student_guardians(session: Session, student_id: int) -> Sequence[StudentGuardian]:
    """Retrieves the guardian link objects for a given student."""
    stmt = select(StudentGuardian).where(StudentGuardian.student_id == student_id)
    return session.exec(stmt).all()

def link_guardian(
    session: Session,
    student_id: int,
    guardian_id: int,
    relationship: str | None = None,
    is_primary: bool = False,
) -> StudentGuardian:
    link = StudentGuardian(
        student_id=student_id,
        guardian_id=guardian_id,
        relationship=relationship,
        is_primary=is_primary,
    )
    apply_create_audit(link)
    session.add(link)
    session.flush()
    return link

def get_siblings(session: Session, student_id: int) -> list[dict]:
    """
    Returns sibling data via ORM joins on StudentGuardian.
    Two-query approach: find shared guardians, then find their other students.
    """
    guardian_links = session.exec(
        select(StudentGuardian).where(StudentGuardian.student_id == student_id)
    ).all()
    guardian_ids = [link.guardian_id for link in guardian_links]
    if not guardian_ids:
        return []

    sibling_links = session.exec(
        select(StudentGuardian)
        .where(StudentGuardian.guardian_id.in_(guardian_ids))
        .where(StudentGuardian.student_id != student_id)
    ).all()
    sibling_ids = {link.student_id for link in sibling_links}

    return [
        {"sibling_id": s.id, "sibling_name": s.full_name}
        for sid in sibling_ids
        if (s := session.get(Student, sid))
    ]

def get_students_by_guardian_id(
    session: Session, guardian_id: int, active_only: bool = True
) -> list[Student]:
    """
    Returns all Student objects linked to a guardian via StudentGuardian.
    Single JOIN — avoids N+1 query anti-pattern.
    """
    stmt = (
        select(Student)
        .join(StudentGuardian, StudentGuardian.student_id == Student.id)
        .where(StudentGuardian.guardian_id == guardian_id)
    )
    if active_only:
        stmt = stmt.where(Student.is_active == True)
    return list(session.exec(stmt).all())
