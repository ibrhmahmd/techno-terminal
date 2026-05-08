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
    level_number: int | None = None,
) -> list[CourseSession]:
    """
    Creates `count` weekly CourseSession records within an existing DB session.
    Does NOT commit — caller is responsible for the transaction boundary.
    Sessions are numbered sequentially starting from 1.

    Args:
        level_number: Explicit level number to assign to the sessions. If None,
                      falls back to group.level_number. Should always be supplied
                      during level progression so that sessions are tagged with
                      the NEW level number before group.level_number is updated.
    """
    resolved_level = level_number if level_number is not None else group.level_number
    created: list[CourseSession] = []
    d = start_date
    for i in range(sessions_count):
        cs = CourseSession(
            group_id=group.id,
            level_number=resolved_level,
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
