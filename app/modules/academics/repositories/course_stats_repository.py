"""
app/modules/academics/repositories/course_stats_repository.py
──────────────────────────────────────────────────────────────
Repository functions for CourseStats analytics view.
"""
from sqlmodel import Session
from sqlalchemy import text
from app.modules.academics.schemas import CourseStatsDTO
from app.modules.academics.constants import VIEW_COURSE_STATS


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
