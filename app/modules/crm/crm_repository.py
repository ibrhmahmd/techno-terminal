from typing import Sequence
from sqlmodel import Session, select
from sqlalchemy import or_
from app.modules.crm.crm_models import Guardian, Student, StudentGuardian
from app.shared.audit_utils import apply_create_audit


# --- Guardian Repository ---


def create_guardian(session: Session, guardian: Guardian) -> Guardian:
    session.add(guardian)
    session.flush()  # Flushes to get the auto-incremented ID without committing
    return guardian


def get_guardian_by_id(session: Session, guardian_id: int) -> Guardian | None:
    return session.get(Guardian, guardian_id)


def get_guardian_by_phone(session: Session, phone: str) -> Guardian | None:
    stmt = select(Guardian).where(Guardian.phone_primary == phone)
    return session.exec(stmt).first()


def get_all_guardians(session: Session, skip: int = 0, limit: int = 200) -> Sequence[Guardian]:
    stmt = select(Guardian).offset(skip).limit(limit)
    return session.exec(stmt).all()


def search_guardians(session: Session, query: str) -> Sequence[Guardian]:
    search_term = f"%{query}%"
    stmt = (
        select(Guardian)
        .where(
            or_(
                Guardian.full_name.ilike(search_term),
                Guardian.phone_primary.ilike(search_term),
                Guardian.phone_secondary.ilike(search_term),
            )
        )
        .limit(50)
    )
    return session.exec(stmt).all()


# --- Student Repository ---


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


def get_student_guardians(
    session: Session, student_id: int
) -> Sequence[StudentGuardian]:
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
    (Replaces raw SQL against v_siblings view — ORM is mockable in tests.)
    """
    # Step 1: find all guardians linked to this student
    guardian_links = session.exec(
        select(StudentGuardian).where(StudentGuardian.student_id == student_id)
    ).all()
    guardian_ids = [link.guardian_id for link in guardian_links]
    if not guardian_ids:
        return []

    # Step 2: find all other students sharing those guardians
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
    Uses a single JOIN instead of a loop — avoids the N+1 query anti-pattern.
    """
    from app.modules.crm.crm_models import StudentGuardian

    stmt = (
        select(Student)
        .join(StudentGuardian, StudentGuardian.student_id == Student.id)
        .where(StudentGuardian.guardian_id == guardian_id)
    )
    if active_only:
        stmt = stmt.where(Student.is_active == True)
    return list(session.exec(stmt).all())


# ── RepositoryProtocol aliases ────────────────────────────────────────────────
# Primary entity: Guardian
get_by_id = get_guardian_by_id
create = create_guardian
list_all = search_guardians  # search_guardians takes (session, query) — closest to list_all
