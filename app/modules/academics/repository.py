from typing import Sequence
from sqlmodel import Session, select
from .models import Course, Group

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


def list_all_active_groups(session: Session) -> Sequence[Group]:
    stmt = select(Group).where(Group.status == "active")
    return session.exec(stmt).all()


def get_group_by_id(session: Session, group_id: int) -> Group | None:
    return session.get(Group, group_id)


# --- Session (CourseSession) Repository ---

from .session_models import CourseSession


def create_session(session: Session, course_session: CourseSession) -> CourseSession:
    session.add(course_session)
    session.flush()
    return course_session


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
