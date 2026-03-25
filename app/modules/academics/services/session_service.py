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
from app.modules.academics.academics_models import Course, Group
from app.modules.academics.academics_session_models import CourseSession
from app.modules.academics.schemas import UpdateSessionDTO
from app.modules.academics.helpers.time_helpers import next_weekday
from app.modules.academics.helpers.session_planning import create_sessions_in_session
from app.modules.academics import repositories as repo


class SessionService:
    def generate_level_sessions(
        self, group_id: int, level_number: int, start_date: date
    ) -> list[CourseSession]:
        """
        Generates N weekly sessions for a group level.
        Raises if sessions for this level already exist.
        ATOMIC — validation + session creation in one transaction.
        """
        with get_session() as session:                          # ← ONE session
            group = repo.get_group_by_id(session, group_id)
            if not group:
                raise NotFoundError(f"Group {group_id} not found.")
            course = session.get(Course, group.course_id)
            if not course:
                raise NotFoundError(f"Course for group {group_id} not found.")

            existing = repo.count_sessions(session, group_id, level_number)
            if existing > 0:
                raise BusinessRuleError(
                    f"Level {level_number} already has {existing} session(s). "
                    "Remove them first or add extra sessions instead."
                )

            snapped = (
                next_weekday(start_date, group.default_day)
                if group.default_day else start_date
            )
            return create_sessions_in_session(                # ← SAME session
                session, group_id, level_number, snapped,
                course.sessions_per_level,
                group.default_time_start, group.default_time_end,
                group.instructor_id,
            )
        # ← SINGLE COMMIT — validation + sessions or nothing

    def add_extra_session(
        self, group_id: int, level_number: int, extra_date: date, notes: str | None = None
    ) -> CourseSession:
        """
        Adds an extra session numbered after the last existing session.
        ATOMIC — session_number is calculated and the new row is inserted in the
        same transaction, eliminating the race condition that previously allowed
        two concurrent requests to compute the same next number.
        """
        with get_session() as session:
            group = repo.get_group_by_id(session, group_id)
            if not group:
                raise NotFoundError(f"Group {group_id} not found.")

            # Atomic: read max session_number from DB within the same transaction
            next_num = repo.get_max_session_number(session, group_id, level_number) + 1

            cs = CourseSession(
                group_id=group_id,
                level_number=level_number,
                session_number=next_num,
                session_date=extra_date,
                start_time=group.default_time_start,
                end_time=group.default_time_end,
                actual_instructor_id=group.instructor_id,
                is_extra_session=True,
                notes=notes,
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

    def advance_group_level(self, group_id: int) -> Group:
        """Increments group.level_number. Call after a level is confirmed complete."""
        with get_session() as session:
            group = repo.increment_group_level(session, group_id)
            if not group:
                raise NotFoundError(f"Group {group_id} not found.")
            return group
