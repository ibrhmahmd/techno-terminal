"""
app/modules/academics/services/session_service.py
──────────────────────────────────────
Service class for Session-related business logic.
"""
from datetime import timedelta

from sqlmodel import select

from app.db.uow import UnitOfWork
from app.shared.audit_utils import apply_create_audit, apply_update_audit
from app.shared.exceptions import NotFoundError, BusinessRuleError
from app.modules.academics.models import Course
from app.modules.academics.models import CourseSession
from app.modules.hr.models import Employee
from app.modules.academics.schemas.session_schemas import UpdateSessionDTO, AddExtraSessionInput
from app.modules.academics.schemas.session_schemas import GenerateLevelSessionsInput
from app.shared.time_helpers import next_weekday
from app.modules.academics.services.session_planning import create_sessions_in_session
from app.modules.academics.constants import (
    SESSION_STATUS_CANCELLED, SESSION_STATUS_SCHEDULED,
)
from app.modules.attendance.models.attendance_models import Attendance

import app.modules.academics.repositories.session_repository as repo
# Note: In a fully isolated slice, fetching group info should ideally go through
# the group core interface. Since session planning is tightly coupled with group
# defaults, we temporarily import the group repository here as per the migration plan.
from app.modules.academics.repositories.group_repository import GroupRepository
import app.modules.academics.repositories.group_level_repository as level_repo


class SessionService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._repo_group = GroupRepository(uow.session)

    def get_session_by_id(self, session_id: int) -> CourseSession:
        """Get a session by ID."""
        cs = repo.get_session_by_id(self._uow.session, session_id)
        if not cs:
            raise NotFoundError(f"Session {session_id} not found")
        return cs

    def list_group_sessions(self, group_id: int, level_number: int | None = None) -> list[CourseSession]:
        """List sessions for a group, optionally filtered by level number.

        When level_number is None, defaults to the group's current active level.
        """
        if level_number is not None:
            return list(repo.list_sessions_by_level(self._uow.session, group_id, level_number))
        active_level = level_repo.get_current_group_level(self._uow.session, group_id)
        if active_level:
            return list(repo.list_sessions_by_group_level(self._uow.session, active_level.id))
        return list(repo.list_sessions_by_group(self._uow.session, group_id))

    def generate_level_sessions(
        self, data: GenerateLevelSessionsInput
    ) -> list[CourseSession]:
        """
        Generates N weekly sessions for a group level.
        Raises if sessions for this level already exist.
        """
        group = self._repo_group.get_group_by_id(data.group_id)
        if not group:
            raise NotFoundError(f"Group {data.group_id} not found.")
        course = self._uow.session.get(Course, group.course_id)
        if not course:
            raise NotFoundError(f"Course for group {data.group_id} not found.")

        existing = repo.count_sessions(self._uow.session, data.group_id, data.level_number)
        if existing > 0:
            raise BusinessRuleError(
                f"Level {data.level_number} already has {existing} session(s). "
                "Remove them first or add extra sessions instead."
            )

        gl_id = repo.get_group_level_id(self._uow.session, data.group_id, data.level_number)

        snapped = (
            next_weekday(data.start_date, group.default_day)
            if group.default_day else data.start_date
        )
        return create_sessions_in_session(
            session=self._uow.session,
            group=group,
            sessions_count=course.sessions_per_level,
            start_date=snapped,
            group_level_id=gl_id,
        )

    def add_extra_session(
        self, data: AddExtraSessionInput
    ) -> CourseSession:
        """Adds an extra session numbered after the last existing session."""
        group = self._repo_group.get_group_by_id(data.group_id)
        if not group:
            raise NotFoundError(f"Group {data.group_id} not found.")

        next_num = repo.get_next_session_number(self._uow.session, data.group_id, data.level_number)

        gl_id = repo.get_group_level_id(self._uow.session, data.group_id, data.level_number)

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
            group_level_id=gl_id,
        )
        apply_create_audit(cs)
        result = repo.create_session(self._uow.session, cs)
        self._uow.commit()
        self._uow.session.refresh(result)
        return result

    def update_session(self, session_id: int, data: UpdateSessionDTO) -> CourseSession:
        cs = repo.get_session_by_id(self._uow.session, session_id)
        if not cs:
            raise NotFoundError(f"Session {session_id} not found.")
        for k, v in data.model_dump(exclude_unset=True).items():
            if hasattr(cs, k) and k != "id":
                setattr(cs, k, v)

        if cs.actual_instructor_id is not None:
            emp = self._uow.session.get(Employee, cs.actual_instructor_id)
            if not emp:
                raise BusinessRuleError(
                    f"Instructor with id={cs.actual_instructor_id} does not exist."
                )
        apply_update_audit(cs)
        self._uow.session.add(cs)
        self._uow.commit()
        self._uow.session.refresh(cs)
        return cs

    def delete_session(self, session_id: int) -> bool:
        res = repo.delete_session(self._uow.session, session_id)
        self._uow.commit()
        return res

    def check_level_complete(self, group_id: int, level_number: int) -> bool:
        """Returns True if all regular sessions for the level exist."""
        group = self._repo_group.get_group_by_id(group_id)
        if not group:
            raise NotFoundError(f"Group {group_id} not found.")
        course = self._uow.session.get(Course, group.course_id)
        if not course:
            raise NotFoundError(f"Course {group.course_id} for group {group_id} not found.")
        count = repo.count_sessions(self._uow.session, group_id, level_number)
        return count >= course.sessions_per_level

    def cancel_session(self, session_id: int) -> CourseSession:

        cs = repo.get_session_by_id(self._uow.session, session_id)
        if not cs:
            raise NotFoundError(f"Session {session_id} not found.")
        if cs.status == SESSION_STATUS_CANCELLED:
            return cs

        cs.status = SESSION_STATUS_CANCELLED
        old_number = cs.session_number
        cs.session_number = 0

        stmt_attendance = select(Attendance).where(Attendance.session_id == session_id)
        attendances = self._uow.session.exec(stmt_attendance).all()
        for att in attendances:
            att.status = SESSION_STATUS_CANCELLED
            self._uow.session.add(att)

        stmt_future = select(CourseSession).where(
            CourseSession.group_id == cs.group_id,
            CourseSession.level_number == cs.level_number,
            CourseSession.session_number > old_number,
            CourseSession.status != SESSION_STATUS_CANCELLED
        ).order_by(CourseSession.session_number)
        future_sessions = self._uow.session.exec(stmt_future).all()

        for fs in future_sessions:
            fs.session_number -= 1
            self._uow.session.add(fs)

        stmt_max = select(CourseSession).where(
            CourseSession.group_id == cs.group_id,
            CourseSession.level_number == cs.level_number
        ).order_by(CourseSession.session_date.desc())
        last_cs = self._uow.session.exec(stmt_max).first()
        tail_date = last_cs.session_date if last_cs else cs.session_date

        max_num = repo.get_next_session_number(self._uow.session, cs.group_id, cs.level_number) - 1

        repl_gl_id = cs.group_level_id or repo.get_group_level_id(self._uow.session, cs.group_id, cs.level_number)

        replacement = CourseSession(
            group_id=cs.group_id,
            level_number=cs.level_number,
            session_number=max_num + 1,
            session_date=tail_date + timedelta(days=7),
            start_time=cs.start_time,
            end_time=cs.end_time,
            actual_instructor_id=cs.actual_instructor_id,
            status=SESSION_STATUS_SCHEDULED,
            group_level_id=repl_gl_id,
        )
        apply_create_audit(replacement)
        apply_update_audit(cs)
        self._uow.session.add(replacement)
        self._uow.session.add(cs)
        self._uow.commit()
        self._uow.session.refresh(cs)
        return cs

    def reactivate_session(self, session_id: int) -> CourseSession:

        cs = repo.get_session_by_id(self._uow.session, session_id)
        if not cs:
            raise NotFoundError(f"Session {session_id} not found")
        if cs.status != SESSION_STATUS_CANCELLED:
            raise BusinessRuleError(f"Session {session_id} is not cancelled")

        stmt_replacement = select(CourseSession).where(
            CourseSession.group_id == cs.group_id,
            CourseSession.level_number == cs.level_number,
            CourseSession.status != SESSION_STATUS_CANCELLED
        ).order_by(CourseSession.session_number.desc())
        replacement = self._uow.session.exec(stmt_replacement).first()

        stmt_all = select(CourseSession).where(
            CourseSession.group_id == cs.group_id,
            CourseSession.level_number == cs.level_number,
            CourseSession.status != SESSION_STATUS_CANCELLED,
            CourseSession.id != cs.id
        ).order_by(CourseSession.session_number.asc())
        all_sessions = self._uow.session.exec(stmt_all).all()

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

        future_sessions = self._uow.session.exec(stmt_future).all()
        for fs in future_sessions:
            fs.session_number += 1
            self._uow.session.add(fs)

        cs.session_number = expected_number
        cs.status = SESSION_STATUS_SCHEDULED
        apply_update_audit(cs)
        self._uow.session.add(cs)

        if replacement:
            self._uow.session.delete(replacement)

        stmt_attendance = select(Attendance).where(Attendance.session_id == session_id)
        attendances = self._uow.session.exec(stmt_attendance).all()
        for att in attendances:
            att.status = "present"
            self._uow.session.add(att)

        self._uow.commit()
        self._uow.session.refresh(cs)
        return cs