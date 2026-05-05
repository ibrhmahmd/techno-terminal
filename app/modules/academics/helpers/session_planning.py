"""
app/modules/academics/helpers/session_planning.py
──────────────────────────────────────────────────
Session generation helper — extracted from academics_service.py.
Pure orchestration: builds CourseSession instances within a given DB session.
No commits. Caller owns the transaction.
"""
from datetime import date, time, timedelta
from sqlmodel import Session
from app.shared.datetime_utils import utc_now
from app.modules.academics.models import CourseSession, Group


def create_sessions_in_session(
    session: Session,
    group: Group,
    sessions_count: int,
    start_date: date,
) -> list[CourseSession]:
    """
    Creates `count` weekly CourseSession records within an existing DB session.
    Does NOT commit — caller is responsible for the transaction boundary.
    Sessions are numbered sequentially starting from 1.
    """
    created: list[CourseSession] = []
    d = start_date
    for i in range(sessions_count):
        cs = CourseSession(
            group_id=group.id,
            level_number=group.level_number,
            session_number=i + 1,
            session_date=d,
            start_time=group.default_time_start,
            end_time=group.default_time_end,
            actual_instructor_id=group.instructor_id,
            is_extra_session=False,
            created_at=utc_now(),
        )
        session.add(cs)
        session.flush()
        created.append(cs)
        d += timedelta(weeks=1)
    return created
