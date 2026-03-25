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
from app.modules.academics.academics_session_models import CourseSession


def create_sessions_in_session(
    session: Session,
    group_id: int,
    level_number: int,
    start_date: date,
    count: int,
    start_time: time,
    end_time: time,
    instructor_id: int,
) -> list[CourseSession]:
    """
    Creates `count` weekly CourseSession records within an existing DB session.
    Does NOT commit — caller is responsible for the transaction boundary.
    Sessions are numbered sequentially starting from 1.
    """
    created: list[CourseSession] = []
    d = start_date
    for i in range(count):
        cs = CourseSession(
            group_id=group_id,
            level_number=level_number,
            session_number=i + 1,
            session_date=d,
            start_time=start_time,
            end_time=end_time,
            actual_instructor_id=instructor_id,
            is_extra_session=False,
            created_at=utc_now(),
        )
        session.add(cs)
        session.flush()
        created.append(cs)
        d += timedelta(weeks=1)
    return created
