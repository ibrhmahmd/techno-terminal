from typing import Sequence
from sqlmodel import Session, select
from sqlalchemy import text
from app.modules.academics.models import Course, Group

# --- Course Repository ---


def create_course(session: Session, course: Course) -> Course:
    session.add(course)
    session.flush()
    return course


def get_course_by_name(session: Session, name: str) -> Course | None:
    stmt = select(Course).where(Course.name == name)
    return session.exec(stmt).first()


def list_active_courses(session: Session) -> Sequence[Course]:
    stmt = select(Course).where(Course.is_active == True)
    return session.exec(stmt).all()


def update_course_price(
    session: Session, course_id: int, new_price: float
) -> Course | None:
    course = session.get(Course, course_id)
    if course:
        course.price_per_level = new_price
        session.add(course)
    return course


# --- Group Repository ---


def create_group(session: Session, group: Group) -> Group:
    session.add(group)
    session.flush()
    return group


def list_groups_by_course(session: Session, course_id: int) -> Sequence[Group]:
    stmt = (
        select(Group)
        .where(Group.course_id == course_id)
        .where(Group.status == "active")
    )
    return session.exec(stmt).all()


def list_all_active_groups(
    session: Session, include_inactive: bool = False
) -> Sequence[Group]:
    stmt = select(Group)
    if not include_inactive:
        stmt = stmt.where(Group.status == "active")
    return session.exec(stmt).all()


def get_group_by_id(session: Session, group_id: int) -> Group | None:
    return session.get(Group, group_id)


def increment_group_level(session: Session, group_id: int) -> Group | None:
    group = session.get(Group, group_id)
    if group:
        group.level_number += 1
        session.add(group)
    return group


def get_enriched_groups(session: Session) -> list[dict]:
    """Returns active groups joined with instructor name and course name for display."""
    stmt = text("""
        SELECT
            g.id,
            g.name AS group_name,
            c.name AS course_name,
            COALESCE(e.full_name, 'Unassigned') AS instructor_name,
            g.level_number,
            g.default_day,
            g.default_time_start,
            g.default_time_end,
            g.max_capacity,
            g.status
        FROM groups g
        JOIN courses c ON g.course_id = c.id
        LEFT JOIN employees e ON g.instructor_id = e.id
        WHERE g.status = 'active'
        ORDER BY g.id
    """)
    result = session.execute(stmt)
    return [dict(row._mapping) for row in result.all()]


def get_enriched_groups_by_date(session: Session, target_date: str) -> list[dict]:
    """Returns active groups that have at least one session on the given date."""
    stmt = text("""
        SELECT DISTINCT
            g.id,
            g.name AS group_name,
            c.name AS course_name,
            COALESCE(e.full_name, 'Unassigned') AS instructor_name,
            g.level_number,
            g.default_day,
            g.default_time_start,
            g.default_time_end,
            g.max_capacity,
            g.status
        FROM groups g
        JOIN courses c ON g.course_id = c.id
        LEFT JOIN employees e ON g.instructor_id = e.id
        JOIN sessions s ON g.id = s.group_id
        WHERE g.status = 'active' AND s.session_date = :target_date
        ORDER BY g.id
    """)
    result = session.execute(stmt, {"target_date": target_date})
    return [dict(row._mapping) for row in result.all()]


# --- Session (CourseSession) Repository ---

from app.modules.academics.session_models import CourseSession


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


def update_session_instructor(
    session: Session, session_id: int, instructor_id: int
) -> CourseSession | None:
    cs = session.get(CourseSession, session_id)
    if cs:
        cs.actual_instructor_id = instructor_id
        cs.is_substitute = True
        session.add(cs)
    return cs
