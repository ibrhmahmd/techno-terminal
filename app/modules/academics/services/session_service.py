"""
app/modules/academics/services/session_service.py
──────────────────────────────────────────────────
Service class for Session-related business logic.
"""
from datetime import date
from app.db.connection import get_session
from app.shared.audit_utils import apply_update_audit
from app.shared.datetime_utils import utc_now
from app.shared.exceptions import NotFoundError, BusinessRuleError
from app.modules.academics.models import Course, Group
from app.modules.academics.models import CourseSession
from app.modules.academics.schemas import UpdateSessionDTO, AddExtraSessionInput, GenerateLevelSessionsInput
from app.modules.academics.helpers.time_helpers import next_weekday
from app.modules.academics.helpers.session_planning import create_sessions_in_session
from app.modules.academics import repositories as repo


class SessionService:
    def get_session_by_id(self, session_id: int) -> CourseSession:
        """
        Get a session by ID.
        
        Args:
            session_id: The session ID
            
        Returns:
            CourseSession entity
            
        Raises:
            NotFoundError: If session not found
        """
        with get_session() as session:
            cs = session.get(CourseSession, session_id)
            if not cs:
                raise NotFoundError(f"Session {session_id} not found")
            return cs

    def generate_level_sessions(
        self, data: GenerateLevelSessionsInput
    ) -> list[CourseSession]:
        """
        Generates N weekly sessions for a group level.
        Raises if sessions for this level already exist.
        ATOMIC — validation + session creation in one transaction.
        """
        with get_session() as session:                          # ← ONE session
            group = repo.get_group_by_id(session, data.group_id)
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
            return create_sessions_in_session(                # ← SAME session
                session, data.group_id, data.level_number, snapped,
                course.sessions_per_level,
                group.default_time_start, group.default_time_end,
                group.instructor_id,
            )
        # ← SINGLE COMMIT — validation + sessions or nothing

    def add_extra_session(
        self, data: AddExtraSessionInput
    ) -> CourseSession:
        """
        Adds an extra session numbered after the last existing session.
        ATOMIC — session_number is calculated and the new row is inserted in the
        same transaction, eliminating the race condition that previously allowed
        two concurrent requests to compute the same next number.
        """
        with get_session() as session:
            group = repo.get_group_by_id(session, data.group_id)
            if not group:
                raise NotFoundError(f"Group {data.group_id} not found.")

            # Atomic: read max session_number from DB within the same transaction
            next_num = repo.get_max_session_number(session, data.group_id, data.level_number) + 1

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
                created_at=utc_now(),
            )
            return repo.create_session(session, cs)
        # ← SINGLE COMMIT — number read + row inserted atomically

    def update_session(self, session_id: int, data: UpdateSessionDTO) -> CourseSession:
        with get_session() as session:
            cs = session.get(CourseSession, session_id)
            if not cs:
                raise NotFoundError(f"Session {session_id} not found.")
            for k, v in data.model_dump(exclude_unset=True).items():
                if hasattr(cs, k) and k != "id":
                    setattr(cs, k, v)
            apply_update_audit(cs)
            session.add(cs)
            session.commit()
            session.refresh(cs)
            return cs

    def delete_session(self, session_id: int) -> bool:
        with get_session() as session:
            return repo.delete_session(session, session_id)

    def mark_substitute_instructor(self, session_id: int, instructor_id: int) -> CourseSession:
        with get_session() as session:
            cs = repo.update_session_instructor(session, session_id, instructor_id)
            if not cs:
                raise NotFoundError(f"Session {session_id} not found.")
            return cs

    def list_group_sessions(
        self, group_id: int, level_number: int | None = None
    ) -> list[CourseSession]:
        with get_session() as session:
            return list(repo.list_sessions(session, group_id, level_number))

    def check_level_complete(self, group_id: int, level_number: int) -> bool:
        """
        Returns True if all regular sessions for the level exist.
        Raises NotFoundError on missing group or course — never silently returns
        False for data integrity issues. False is reserved for 'level genuinely
        not yet complete'.
        """
        with get_session() as session:
            group = repo.get_group_by_id(session, group_id)
            if not group:
                raise NotFoundError(f"Group {group_id} not found.")
            course = session.get(Course, group.course_id)
            if not course:
                raise NotFoundError(
                    f"Course {group.course_id} for group {group_id} not found. "
                    "Data integrity issue — verify the groups table."
                )
            count = repo.count_sessions(session, group_id, level_number)
            return count >= course.sessions_per_level

    def progress_group_level(self, group_id: int) -> Group:
        """
        Increments group level, inflates enrollment amount_due for the new level,
        and automatically generates the block of sessions.
        """
        from app.modules.enrollments.models.enrollment_models import Enrollment
        from sqlmodel import select
        from app.modules.academics.helpers.time_helpers import next_weekday
        
        with get_session() as session:
            group = repo.increment_group_level(session, group_id)
            if not group:
                raise NotFoundError(f"Group {group_id} not found.")
                
            course = session.get(Course, group.course_id)
            
            # Sub-Phase: Increment active enrollments & bill them for the new level
            stmt = select(Enrollment).where(
                Enrollment.group_id == group_id, 
                Enrollment.status == "active"
            )
            enrollments = session.exec(stmt).all()
            for e in enrollments:
                e.level_number = group.level_number
                e.amount_due = float(e.amount_due or 0) + float(course.price_per_level)
                session.add(e)
                
            # Sub-Phase: Generate sessions for the new level
            start_dt = next_weekday(date.today(), group.default_day) if group.default_day else date.today()
            create_sessions_in_session(
                session, group_id, group.level_number, start_dt,
                course.sessions_per_level,
                group.default_time_start, group.default_time_end,
                group.instructor_id,
            )
            session.commit()
            return group

    def cancel_session(self, session_id: int) -> CourseSession:
        """
        Flags session as cancelled.
        Updates all attendance records for this session to 'cancelled' status.
        Cascades the session number downwards onto future sessions so numbering isn't broken.
        Appends exactly one new session at the tail to maintain course density compliance.
        """
        from sqlmodel import select
        from datetime import timedelta
        
        with get_session() as session:
            cs = session.get(CourseSession, session_id)
            if not cs:
                raise NotFoundError(f"Session {session_id} not found.")
            if cs.status == "cancelled":
                return cs
                
            cs.status = "cancelled"
            old_number = cs.session_number
            cs.session_number = 0  # detach from strictly ordered numbering
            
            # Update all attendances for this session to 'cancelled'
            from app.modules.attendance.models.attendance_models import Attendance
            stmt_attendance = select(Attendance).where(Attendance.session_id == session_id)
            attendances = session.exec(stmt_attendance).all()
            for att in attendances:
                att.status = "cancelled"
                session.add(att)
            
            # Find future sessions to slide numbers down by 1
            stmt_future = select(CourseSession).where(
                CourseSession.group_id == cs.group_id,
                CourseSession.level_number == cs.level_number,
                CourseSession.session_number > old_number,
                CourseSession.status != "cancelled"
            ).order_by(CourseSession.session_number)
            future_sessions = session.exec(stmt_future).all()
            
            for fs in future_sessions:
                fs.session_number -= 1
                session.add(fs)
                
            # Determine tail date for a replacement session
            stmt_max = select(CourseSession).where(
                CourseSession.group_id == cs.group_id,
                CourseSession.level_number == cs.level_number
            ).order_by(CourseSession.session_date.desc())
            last_cs = session.exec(stmt_max).first()
            tail_date = last_cs.session_date if last_cs else cs.session_date
            
            course = session.get(Course, session.get(Group, cs.group_id).course_id)
            
            # Recalculate max number to safely append
            max_num = repo.get_max_session_number(session, cs.group_id, cs.level_number)
            
            replacement = CourseSession(
                group_id=cs.group_id,
                level_number=cs.level_number,
                session_number=max_num + 1,
                session_date=tail_date + timedelta(days=7),
                start_time=cs.start_time,
                end_time=cs.end_time,
                actual_instructor_id=cs.actual_instructor_id,
                status="scheduled"
            )
            
            session.add(replacement)
            session.add(cs)
            session.commit()
            session.refresh(cs)
            return cs

    def reactivate_session(self, session_id: int) -> CourseSession:
        """
        Reactivate a previously cancelled session.
        Restores session by shifting future sessions up by 1.
        Deletes the replacement session that was created at cancellation.
        Restores attendance records to 'present' status.
        """
        from sqlmodel import select
        from datetime import timedelta
        
        with get_session() as session:
            cs = session.get(CourseSession, session_id)
            if not cs:
                raise NotFoundError(f"Session {session_id} not found")
            if cs.status != "cancelled":
                raise BusinessRuleError(f"Session {session_id} is not cancelled (status: {cs.status})")
            
            # Get the replacement session (the one with the highest session_number for this level)
            stmt_replacement = select(CourseSession).where(
                CourseSession.group_id == cs.group_id,
                CourseSession.level_number == cs.level_number,
                CourseSession.status != "cancelled"
            ).order_by(CourseSession.session_number.desc())
            replacement = session.exec(stmt_replacement).first()
            
            # Find the gap in session numbers to determine where to reinsert
            # Get all active sessions ordered by session_number
            stmt_all = select(CourseSession).where(
                CourseSession.group_id == cs.group_id,
                CourseSession.level_number == cs.level_number,
                CourseSession.status != "cancelled",
                CourseSession.id != cs.id
            ).order_by(CourseSession.session_number.asc())
            all_sessions = session.exec(stmt_all).all()
            
            # Find the first gap in numbering
            expected_number = 1
            for s in all_sessions:
                if s.session_number > expected_number:
                    break
                expected_number += 1
            
            # Shift future sessions up by 1 (in reverse order to avoid conflicts)
            stmt_future = select(CourseSession).where(
                CourseSession.group_id == cs.group_id,
                CourseSession.level_number == cs.level_number,
                CourseSession.session_number >= expected_number,
                CourseSession.status != "cancelled"
            ).order_by(CourseSession.session_number.desc())
            
            future_sessions = session.exec(stmt_future).all()
            for fs in future_sessions:
                fs.session_number += 1
                session.add(fs)
            
            # Restore the cancelled session
            cs.session_number = expected_number
            cs.status = "scheduled"
            session.add(cs)
            
            # Delete the replacement session if it exists
            if replacement:
                session.delete(replacement)
            
            # Restore attendances to 'present' status
            from app.modules.attendance.models.attendance_models import Attendance
            stmt_attendance = select(Attendance).where(Attendance.session_id == session_id)
            attendances = session.exec(stmt_attendance).all()
            for att in attendances:
                att.status = "present"
                session.add(att)
            
            session.commit()
            session.refresh(cs)
            return cs
