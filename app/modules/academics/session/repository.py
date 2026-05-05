"""
app/modules/academics/session/repository.py
─────────────────────────────────────────
Repository functions for the Session slice.
"""
from typing import Sequence
from datetime import date
from sqlmodel import Session, select, func
from app.modules.academics.models import CourseSession


def get_session_by_id(session: Session, session_id: int) -> CourseSession | None:
    return session.get(CourseSession, session_id)


def list_sessions_by_group(
    session: Session, group_id: int, include_cancelled: bool = False
) -> Sequence[CourseSession]:
    stmt = select(CourseSession).where(CourseSession.group_id == group_id)
    if not include_cancelled:
        stmt = stmt.where(CourseSession.status != "cancelled")
    stmt = stmt.order_by(CourseSession.session_date, CourseSession.start_time)
    return session.exec(stmt).all()


def list_sessions_by_level(
    session: Session, group_id: int, level_number: int
) -> Sequence[CourseSession]:
    stmt = (
        select(CourseSession)
        .where(
            CourseSession.group_id == group_id,
            CourseSession.level_number == level_number,
        )
        .order_by(CourseSession.session_number)
    )
    return session.exec(stmt).all()


def count_sessions(session: Session, group_id: int, level_number: int) -> int:
    stmt = select(func.count(CourseSession.id)).where(
        CourseSession.group_id == group_id,
        CourseSession.level_number == level_number,
        CourseSession.status != "cancelled"
    )
    result = session.exec(stmt).first()
    return result or 0


def create_session(session: Session, course_session: CourseSession) -> CourseSession:
    session.add(course_session)
    session.flush()
    return course_session


def get_next_session_number(session: Session, group_id: int, level_number: int) -> int:
    stmt = select(func.max(CourseSession.session_number)).where(
        CourseSession.group_id == group_id,
        CourseSession.level_number == level_number
    )
    max_num = session.exec(stmt).first()
    return (max_num or 0) + 1


def get_todays_sessions(
    session: Session, specific_date: date | None = None
) -> Sequence[CourseSession]:
    """Returns sessions for today or a specific date."""
    target_date = specific_date or date.today()
    stmt = (
        select(CourseSession)
        .where(CourseSession.session_date == target_date)
        .order_by(CourseSession.start_time)
    )
    return session.exec(stmt).all()


def delete_session(session: Session, session_id: int) -> bool:
    cs = session.get(CourseSession, session_id)
    if cs:
        session.delete(cs)
        return True
    return False
