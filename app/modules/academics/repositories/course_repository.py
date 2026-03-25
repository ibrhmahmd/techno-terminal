"""
app/modules/academics/repositories/course_repository.py
────────────────────────────────────────────────────────
Repository functions for the Course entity.
"""
from typing import Sequence
from sqlmodel import Session, select
from app.modules.academics.academics_models import Course


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


def get_course_by_id(session: Session, course_id: int) -> Course | None:
    """Get a course by primary key — satisfies RepositoryProtocol.get_by_id."""
    return session.get(Course, course_id)


# ── RepositoryProtocol aliases ────────────────────────────────────────────────
# Primary entity: Course
get_by_id = get_course_by_id
create = create_course
list_all = list_active_courses
