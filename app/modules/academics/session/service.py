"""
app/modules/academics/session/service.py
──────────────────────────────────────
Service class for Session-related business logic.
"""
from app.db.connection import get_session
from app.shared.audit_utils import apply_update_audit
from app.shared.datetime_utils import utc_now
from app.shared.exceptions import NotFoundError, BusinessRuleError
from app.modules.academics.models import Course, Group
from app.modules.academics.models import CourseSession
from app.modules.hr.models import Employee
from app.modules.academics.session.schemas import UpdateSessionDTO, AddExtraSessionInput
from app.modules.academics.session.schemas import GenerateLevelSessionsInput
from app.modules.academics.helpers.time_helpers import next_weekday
from app.modules.academics.helpers.session_planning import create_sessions_in_session
from app.modules.academics.constants import (
    SESSION_STATUS_CANCELLED, SESSION_STATUS_SCHEDULED,
)
from app.modules.attendance.models.attendance_models import Attendance

import app.modules.academics.session.repository as repo
# Note: In a fully isolated slice, fetching group info should ideally go through 
# the group core interface. Since session planning is tightly coupled with group
# defaults, we temporarily import the group repository here as per the migration plan.
import app.modules.academics.group.core.repository as group_repo


class SessionService:
    def get_session_by_id(self, session_id: int) -> CourseSession:
        """Get a session by ID."""
        with get_session() as session:
            cs = repo.get_session_by_id(session, session_id)
            if not cs:
                raise NotFoundError(f"Session {session_id} not found")
            return cs

    def get_sessions_by_group(self, group_id: int, include_cancelled: bool = False) -> list[CourseSession]:
        with get_session() as session:
            return list(repo.list_sessions_by_group(session, group_id, include_cancelled))

    def list_group_sessions(self, group_id: int, level_number: int | None = None) -> list[CourseSession]:
        """List sessions for a group, optionally filtered by level number."""
        with get_session() as session:
            if level_number is not None:
                return list(repo.list_sessions_by_level(session, group_id, level_number))
            return list(repo.list_sessions_by_group(session, group_id))

    def generate_level_sessions(
        self, data: GenerateLevelSessionsInput
    ) -> list[CourseSession]:
        """
        Generates N weekly sessions for a group level.
        Raises if sessions for this level already exist.
        """
        with get_session() as session:
            group = group_repo.get_group_by_id(session, data.group_id)
            if not group:
                raise NotFoundError(f"Group {data.group_id} not found.")
            course = session.get(Course, group.course_id)
            if not course:
                raise NotFoundError(f"Course for group {data.group_id} not found.")

            existing = repo.count_sessions(session, data.group_id, data.level_number)
            if existing > 0:
                raise BusinessRuleError(
                    f"Level {data.level_number} already has {existing} session(s). "
                    "Remove them first or add extra sessions instead."
                )

            snapped = (
                next_weekday(data.start_date, group.default_day)
                if group.default_day else data.start_date
            )
            return create_sessions_in_session(
                session=session,
                group=group,
                sessions_count=course.sessions_per_level,
                start_date=snapped,
            )

    def add_extra_session(
        self, data: AddExtraSessionInput
    ) -> CourseSession:
        """Adds an extra session numbered after the last existing session."""
        with get_session() as session:
            group = group_repo.get_group_by_id(session, data.group_id)
            if not group:
                raise NotFoundError(f"Group {data.group_id} not found.")

            next_num = repo.get_next_session_number(session, data.group_id, data.level_number)

            cs = CourseSession(
                group_id=data.group_id,
                level_number=data.level_number,
                session_number=next_num,
                session_date=data.extra_date,
                start_time=group.default_time_start,
                end_time=group.default_time_end,
                actual_instructor_id=group.instructor_id,
                is_extra_session=True,
                notes=data.notes,
            )
            from app.shared.audit_utils import apply_create_audit
            apply_create_audit(cs)
            return repo.create_session(session, cs)

    def update_session(self, session_id: int, data: UpdateSessionDTO) -> CourseSession:
        with get_session() as session:
            cs = repo.get_session_by_id(session, session_id)
            if not cs:
                raise NotFoundError(f"Session {session_id} not found.")
            for k, v in data.model_dump(exclude_unset=True).items():
                if hasattr(cs, k) and k != "id":
                    setattr(cs, k, v)
            
            if cs.actual_instructor_id is not None:
                emp = session.get(Employee, cs.actual_instructor_id)
                if not emp:
                    raise BusinessRuleError(
                        f"Instructor with id={cs.actual_instructor_id} does not exist."
                    )
            apply_update_audit(cs)
            session.add(cs)
            session.commit()
            session.refresh(cs)
            return cs

    def delete_session(self, session_id: int) -> bool:
        with get_session() as session:
            res = repo.delete_session(session, session_id)
            session.commit()
            return res

    def check_level_complete(self, group_id: int, level_number: int) -> bool:
        """Returns True if all regular sessions for the level exist."""
        with get_session() as session:
            group = group_repo.get_group_by_id(session, group_id)
            if not group:
                raise NotFoundError(f"Group {group_id} not found.")
            course = session.get(Course, group.course_id)
            if not course:
                raise NotFoundError(f"Course {group.course_id} for group {group_id} not found.")
            count = repo.count_sessions(session, group_id, level_number)
            return count >= course.sessions_per_level

    def cancel_session(self, session_id: int) -> CourseSession:
        from sqlmodel import select
        from datetime import timedelta
        
        with get_session() as session:
            cs = repo.get_session_by_id(session, session_id)
            if not cs:
                raise NotFoundError(f"Session {session_id} not found.")
            if cs.status == SESSION_STATUS_CANCELLED:
                return cs
                
            cs.status = SESSION_STATUS_CANCELLED
            old_number = cs.session_number
            cs.session_number = 0
            
            stmt_attendance = select(Attendance).where(Attendance.session_id == session_id)
            attendances = session.exec(stmt_attendance).all()
            for att in attendances:
                att.status = SESSION_STATUS_CANCELLED
                session.add(att)
            
            stmt_future = select(CourseSession).where(
                CourseSession.group_id == cs.group_id,
                CourseSession.level_number == cs.level_number,
                CourseSession.session_number > old_number,
                CourseSession.status != SESSION_STATUS_CANCELLED
            ).order_by(CourseSession.session_number)
            future_sessions = session.exec(stmt_future).all()
            
            for fs in future_sessions:
                fs.session_number -= 1
                session.add(fs)
                
            stmt_max = select(CourseSession).where(
                CourseSession.group_id == cs.group_id,
                CourseSession.level_number == cs.level_number
            ).order_by(CourseSession.session_date.desc())
            last_cs = session.exec(stmt_max).first()
            tail_date = last_cs.session_date if last_cs else cs.session_date
            
            max_num = repo.get_next_session_number(session, cs.group_id, cs.level_number) - 1
            
            replacement = CourseSession(
                group_id=cs.group_id,
                level_number=cs.level_number,
                session_number=max_num + 1,
                session_date=tail_date + timedelta(days=7),
                start_time=cs.start_time,
                end_time=cs.end_time,
                actual_instructor_id=cs.actual_instructor_id,
                status=SESSION_STATUS_SCHEDULED
            )
            from app.shared.audit_utils import apply_create_audit, apply_update_audit
            apply_create_audit(replacement)
            apply_update_audit(cs)
            session.add(replacement)
            session.add(cs)
            session.commit()
            session.refresh(cs)
            return cs

    def reactivate_session(self, session_id: int) -> CourseSession:
        from sqlmodel import select
        
        with get_session() as session:
            cs = repo.get_session_by_id(session, session_id)
            if not cs:
                raise NotFoundError(f"Session {session_id} not found")
            if cs.status != SESSION_STATUS_CANCELLED:
                raise BusinessRuleError(f"Session {session_id} is not cancelled")
            
            stmt_replacement = select(CourseSession).where(
                CourseSession.group_id == cs.group_id,
                CourseSession.level_number == cs.level_number,
                CourseSession.status != SESSION_STATUS_CANCELLED
            ).order_by(CourseSession.session_number.desc())
            replacement = session.exec(stmt_replacement).first()
            
            stmt_all = select(CourseSession).where(
                CourseSession.group_id == cs.group_id,
                CourseSession.level_number == cs.level_number,
                CourseSession.status != SESSION_STATUS_CANCELLED,
                CourseSession.id != cs.id
            ).order_by(CourseSession.session_number.asc())
            all_sessions = session.exec(stmt_all).all()
            
            expected_number = 1
            for s in all_sessions:
                if s.session_number > expected_number:
                    break
                expected_number += 1
            
            stmt_future = select(CourseSession).where(
                CourseSession.group_id == cs.group_id,
                CourseSession.level_number == cs.level_number,
                CourseSession.session_number >= expected_number,
                CourseSession.status != SESSION_STATUS_CANCELLED
            ).order_by(CourseSession.session_number.desc())
            
            future_sessions = session.exec(stmt_future).all()
            for fs in future_sessions:
                fs.session_number += 1
                session.add(fs)
            
            cs.session_number = expected_number
            cs.status = SESSION_STATUS_SCHEDULED
            from app.shared.audit_utils import apply_update_audit
            apply_update_audit(cs)
            session.add(cs)
            
            if replacement:
                session.delete(replacement)
            
            stmt_attendance = select(Attendance).where(Attendance.session_id == session_id)
            attendances = session.exec(stmt_attendance).all()
            for att in attendances:
                att.status = "present"
                session.add(att)
            
            session.commit()
            session.refresh(cs)
            return cs
