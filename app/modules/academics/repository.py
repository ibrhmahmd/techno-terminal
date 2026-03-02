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
