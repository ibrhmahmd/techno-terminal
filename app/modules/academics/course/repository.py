"""
app/modules/academics/course/repository.py
────────────────────────────────────────
Repository functions for the Course slice.
"""
from typing import Sequence
from sqlmodel import Session, select
from sqlalchemy import text
from app.modules.academics.models import Course
from app.modules.academics.course.schemas import CourseStatsDTO
from app.modules.academics.constants import VIEW_COURSE_STATS


# ── Course CRUD ──────────────────────────────────────────────────────────────

def create_course(session: Session, course: Course) -> Course:
    session.add(course)
    session.flush()
    return course


def get_course_by_name(session: Session, name: str) -> Course | None:
    stmt = select(Course).where(Course.name == name)
    return session.exec(stmt).first()


def list_active_courses(session: Session) -> Sequence[Course]:
    stmt = select(Course).where(Course.is_active.is_(True))
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
    return session.get(Course, course_id)


# ── Course Stats ─────────────────────────────────────────────────────────────

def get_all_course_stats(session: Session) -> list[CourseStatsDTO]:
    """
    Returns aggregate stats for ALL courses from v_course_stats.
    Single query — safe to call for the overview table (no N+1).
    """
    stmt = text(f"""
        SELECT
            course_id,
            course_name,
            total_groups,
            active_groups,
            total_students_ever,
            active_students
        FROM {VIEW_COURSE_STATS}
        ORDER BY course_name
    """)
    result = session.execute(stmt)
    return [CourseStatsDTO(**dict(row._mapping)) for row in result.all()]


def get_course_stats(session: Session, course_id: int) -> CourseStatsDTO | None:
    """
    Returns aggregate stats for a single course from v_course_stats.
    Returns None if course_id does not exist in the view.
    """
    stmt = text(f"""
        SELECT
            course_id,
            course_name,
            total_groups,
            active_groups,
            total_students_ever,
            active_students
        FROM {VIEW_COURSE_STATS}
        WHERE course_id = :course_id
    """)
    result = session.execute(stmt, {"course_id": course_id})
    row = result.first()
    return CourseStatsDTO(**dict(row._mapping)) if row else None 
