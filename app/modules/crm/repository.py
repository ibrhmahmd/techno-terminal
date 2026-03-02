from typing import Sequence
from sqlmodel import Session, select
from sqlalchemy import or_
from .models import Guardian, Student, StudentGuardian


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


def search_students(session: Session, query: str) -> Sequence[Student]:
    search_term = f"%{query}%"
    stmt = select(Student).where(Student.full_name.ilike(search_term)).limit(50)
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
    session.add(link)
    session.flush()
    return link


from sqlalchemy import text


def get_siblings(session: Session, student_id: int) -> list[dict]:
    stmt = text(
        "SELECT sibling_id, sibling_name FROM v_siblings WHERE student_id = :student_id"
    )
    result = session.execute(stmt, {"student_id": student_id})
    # Check if we have results, mapping to dictionaries
    return [dict(row._mapping) for row in result.all()]
