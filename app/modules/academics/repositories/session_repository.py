"""
app/modules/academics/repositories/session_repository.py
─────────────────────────────────────────────────────────
Repository functions for the CourseSession entity.
"""
from typing import Sequence
from sqlmodel import Session, select
from sqlalchemy import func
from app.modules.academics.academics_session_models import CourseSession


def create_session(session: Session, course_session: CourseSession) -> CourseSession:
    session.add(course_session)
    session.flush()
    return course_session


def delete_session(session: Session, session_id: int) -> bool:
    cs = session.get(CourseSession, session_id)
    if cs:
        session.delete(cs)
        return True
    return False


def list_sessions(
    session: Session, group_id: int, level_number: int | None = None
) -> Sequence[CourseSession]:
    stmt = select(CourseSession).where(CourseSession.group_id == group_id)
    if level_number is not None:
        stmt = stmt.where(CourseSession.level_number == level_number)
    stmt = stmt.order_by(CourseSession.level_number, CourseSession.session_number)
    return session.exec(stmt).all()


def get_session_by_id(session: Session, session_id: int) -> CourseSession | None:
    return session.get(CourseSession, session_id)


def count_sessions(session: Session, group_id: int, level_number: int) -> int:
    """Count regular (non-extra) sessions for a group level."""
    stmt = (
        select(CourseSession)
        .where(CourseSession.group_id == group_id)
        .where(CourseSession.level_number == level_number)
        .where(CourseSession.is_extra_session == False)
    )
    return len(session.exec(stmt).all())


def get_max_session_number(
    session: Session, group_id: int, level_number: int
) -> int:
    """
    Returns the current maximum session_number for a group/level using a
    DB-level aggregate.
    """
    stmt = (
        select(func.max(CourseSession.session_number))
        .where(CourseSession.group_id == group_id)
        .where(CourseSession.level_number == level_number)
    )
    result = session.exec(stmt).one()
    # SQLModel func.max returning None instead of 0 if table is empty
    return result if result is not None else 0


def update_session_instructor(
    session: Session, session_id: int, instructor_id: int
) -> CourseSession | None:
    cs = session.get(CourseSession, session_id)
    if cs:
        cs.actual_instructor_id = instructor_id
        cs.is_substitute = True
        session.add(cs)
    return cs
