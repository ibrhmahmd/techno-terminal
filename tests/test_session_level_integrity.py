import time as _time
import pytest
from datetime import date, time


def _unique(name: str) -> str:
    return f"{name}-{_time.time_ns()}"
from app.modules.academics.models import Course, Group, CourseSession
from app.modules.academics.models.group_level_models import GroupLevel
from app.modules.academics.helpers.session_planning import create_sessions_in_session
from app.modules.academics.session.repository import (
    get_group_level_id, list_sessions_by_group_level,
)
from app.modules.academics.session.service import SessionService
from app.modules.academics.group.lifecycle.service import GroupLifecycleService
from app.modules.academics.group.lifecycle.schemas import (
    CreateGroupWithLevelDTO, ProgressLevelDTO, CreateGroupLevelDTO,
)
from app.modules.academics.group.core.schemas import ScheduleGroupInput
from app.modules.academics.group.details.service import GroupDetailsService
from app.modules.academics.course.schemas import AddNewCourseInput, UpdateCourseDTO, MAX_SESSIONS_PER_LEVEL, MAX_LEVELS
from app.modules.academics.course.service import CourseService
from app.shared.exceptions import ValidationError
from sqlmodel import Session, select


class TestRepoHelpers:
    """Unit tests for new repository methods (T011-01 coverage)."""

    def test_create_sessions_in_session_with_group_level_id(self, db_session):
        """T011-01: create_sessions_in_session with group_level_id param."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session, name=_unique("T011-01"))
        group = create_test_group(db_session, course_id=course.id)

        level = GroupLevel(
            group_id=group.id, level_number=1, course_id=course.id,
            sessions_planned=4, status="active",
        )
        db_session.add(level)
        db_session.flush()

        sessions = create_sessions_in_session(
            session=db_session, group=group, sessions_count=2,
            start_date=date.today(), group_level_id=level.id,
        )

        assert len(sessions) == 2
        for s in sessions:
            assert s.group_level_id == level.id

    def test_create_sessions_without_group_level_id(self, db_session):
        """group_level_id defaults to None when not provided."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session, name=_unique("T011-01b"))
        group = create_test_group(db_session, course_id=course.id)

        sessions = create_sessions_in_session(
            session=db_session, group=group, sessions_count=1,
            start_date=date.today(),
        )
        assert sessions[0].group_level_id is None

    def test_get_group_level_id_found(self, db_session):
        """get_group_level_id returns correct ID when match exists."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session, name=_unique("T011-gl"))
        group = create_test_group(db_session, course_id=course.id)
        level = GroupLevel(
            group_id=group.id, level_number=1, course_id=course.id,
            sessions_planned=4, status="active",
        )
        db_session.add(level)
        db_session.flush()

        result = get_group_level_id(db_session, group.id, 1)
        assert result == level.id

    def test_get_group_level_id_not_found(self, db_session):
        """get_group_level_id returns None when no match."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session, name=_unique("T011-gl2"))
        group = create_test_group(db_session, course_id=course.id)
        result = get_group_level_id(db_session, group.id, 999)
        assert result is None

    def test_list_sessions_by_group_level(self, db_session):
        """list_sessions_by_group_level returns only matching sessions."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session, name=_unique("T011-list"))
        group = create_test_group(db_session, course_id=course.id)

        level1 = GroupLevel(
            group_id=group.id, level_number=1, course_id=course.id,
            sessions_planned=4, status="active",
        )
        level2 = GroupLevel(
            group_id=group.id, level_number=2, course_id=course.id,
            sessions_planned=4, status="active",
        )
        db_session.add(level1)
        db_session.add(level2)
        db_session.flush()

        s1 = CourseSession(
            group_id=group.id, level_number=1, session_number=1,
            session_date=date.today(), start_time=time(9), end_time=time(10),
            group_level_id=level1.id,
        )
        s2 = CourseSession(
            group_id=group.id, level_number=2, session_number=1,
            session_date=date.today(), start_time=time(10), end_time=time(11),
            group_level_id=level2.id,
        )
        db_session.add(s1)
        db_session.add(s2)
        db_session.commit()

        result = list_sessions_by_group_level(db_session, level1.id)
        assert len(result) == 1
        assert result[0].id == s1.id


class TestSessionService:
    """Tests for session.service.py changes (T011-02 through T011-06 coverage)."""

    def _setup_group_with_levels(self, db_session, course):
        from tests.utils.db_helpers import create_test_group
        group = create_test_group(db_session, course_id=course.id, level_number=2)
        l1 = GroupLevel(
            group_id=group.id, level_number=1, course_id=course.id,
            sessions_planned=4, status="completed",
        )
        l2 = GroupLevel(
            group_id=group.id, level_number=2, course_id=course.id,
            sessions_planned=4, status="active",
        )
        db_session.add(l1)
        db_session.add(l2)
        db_session.flush()
        for i in range(3):
            db_session.add(CourseSession(
                group_id=group.id, level_number=1, session_number=i + 1,
                session_date=date(2024, 1, i + 1),
                start_time=time(9), end_time=time(10),
                group_level_id=l1.id, status="completed",
            ))
        for i in range(2):
            db_session.add(CourseSession(
                group_id=group.id, level_number=2, session_number=i + 1,
                session_date=date(2025, 6, i + 1),
                start_time=time(9), end_time=time(10),
                group_level_id=l2.id, status="scheduled",
            ))
        db_session.commit()
        return group, l1, l2

    def _create_course(self) -> Course:
        svc = CourseService()
        return svc.add_new_course(AddNewCourseInput(
            name=f"T011-05 Course {id(self)}", category="software",
            price_per_level=500, sessions_per_level=4,
        ))

    def test_list_group_sessions_defaults_to_current_level(self, db_session):
        """T011-05: Default session list returns only current active level."""
        course = self._create_course()
        group, l1, l2 = self._setup_group_with_levels(db_session, course)

        sess_svc = SessionService()
        result = sess_svc.list_group_sessions(group.id)

        assert len(result) == 2
        for s in result:
            assert s.level_number == 2

    def test_list_group_sessions_explicit_level(self, db_session):
        """T011-06: Explicit level filter returns historical sessions."""
        course = self._create_course()
        group, l1, l2 = self._setup_group_with_levels(db_session, course)

        sess_svc = SessionService()
        result = sess_svc.list_group_sessions(group.id, level_number=1)

        assert len(result) == 3
        for s in result:
            assert s.level_number == 1


class TestGroupDetailsService:
    """Tests for details/service.py changes (T011-09 coverage)."""

    def test_get_levels_detailed_defaults_to_current_level(self, db_session):
        """T011-09: get_levels_detailed returns only current level by default."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session, name=_unique("T011-09"))
        group = create_test_group(db_session, course_id=course.id, level_number=2)

        l1 = GroupLevel(
            group_id=group.id, level_number=1, course_id=course.id,
            sessions_planned=4, status="completed",
        )
        l2 = GroupLevel(
            group_id=group.id, level_number=2, course_id=course.id,
            sessions_planned=4, status="active",
        )
        db_session.add(l1)
        db_session.add(l2)
        db_session.commit()

        details_svc = GroupDetailsService()
        result = details_svc.get_levels_detailed(group.id)

        assert len(result.levels) == 1
        assert result.levels[0].level_number == 2

    def test_get_levels_detailed_specific_level(self, db_session):
        """Explicit level_number still returns that specific level."""
        from tests.utils.db_helpers import create_test_course, create_test_group
        course = create_test_course(db_session, name=_unique("T011-09b"))
        group = create_test_group(db_session, course_id=course.id, level_number=2)

        l1 = GroupLevel(
            group_id=group.id, level_number=1, course_id=course.id,
            sessions_planned=4, status="completed",
        )
        l2 = GroupLevel(
            group_id=group.id, level_number=2, course_id=course.id,
            sessions_planned=4, status="active",
        )
        db_session.add(l1)
        db_session.add(l2)
        db_session.commit()

        details_svc = GroupDetailsService()
        result = details_svc.get_levels_detailed(group.id, level_number=1)

        assert len(result.levels) == 1
        assert result.levels[0].level_number == 1


class TestCourseValidation:
    """Tests for course schemas validation (T011-07, T011-08 coverage)."""

    def test_reject_sessions_per_level_over_max(self):
        """T011-07: Course creation rejects sessions_per_level > 100."""
        with pytest.raises(ValidationError) as exc:
            AddNewCourseInput(
                name="Bad Course", category="software",
                price_per_level=500, sessions_per_level=MAX_SESSIONS_PER_LEVEL + 1,
            )
        assert "not exceed" in str(exc.value)

    def test_accept_sessions_per_level_at_max(self):
        """sessions_per_level at exactly MAX is accepted."""
        inp = AddNewCourseInput(
            name="Max Course", category="software",
            price_per_level=500, sessions_per_level=MAX_SESSIONS_PER_LEVEL,
        )
        assert inp.sessions_per_level == MAX_SESSIONS_PER_LEVEL

    def test_reject_max_levels_over_max(self):
        """T011-08: Course creation rejects max_levels > 100."""
        with pytest.raises(ValidationError):
            AddNewCourseInput(
                name="Bad Levels", category="software",
                price_per_level=500, sessions_per_level=10,
                max_levels=MAX_LEVELS + 1,
            )

    def test_accept_valid_max_levels(self):
        """Valid max_levels is accepted."""
        inp = AddNewCourseInput(
            name="Good Levels", category="software",
            price_per_level=500, sessions_per_level=10,
            max_levels=50,
        )
        assert inp.max_levels == 50

    def test_update_dto_rejects_sessions_over_max(self):
        """UpdateCourseDTO also rejects sessions_per_level > 100."""
        with pytest.raises(ValidationError) as exc:
            UpdateCourseDTO(sessions_per_level=MAX_SESSIONS_PER_LEVEL + 1)
        assert "not exceed" in str(exc.value)

    def test_update_dto_accepts_valid_sessions(self):
        """UpdateCourseDTO accepts valid sessions_per_level."""
        dto = UpdateCourseDTO(sessions_per_level=24)
        assert dto.sessions_per_level == 24

    def test_update_dto_rejects_max_levels_over_max(self):
        """UpdateCourseDTO rejects max_levels > 100."""
        with pytest.raises(ValidationError) as exc:
            UpdateCourseDTO(max_levels=MAX_LEVELS + 1)
        assert "not exceed" in str(exc.value)


class TestLifecycleService:
    """Integration tests for lifecycle/service.py (T011-INT-01 coverage)."""

    _emp_counter = 0

    def _create_employee(self, db_session):
        TestLifecycleService._emp_counter += 1
        counter = TestLifecycleService._emp_counter
        from app.modules.hr.models import Employee
        from datetime import datetime
        emp = Employee(
            full_name=f"Test Instructor {counter}",
            phone=f"+2010000000{counter:03d}",
            national_id=f"{10000000000000 + counter}",
            university="Test University",
            major="Computer Science",
            hired_at=datetime.now(tz=None),
            employment_type="part_time",
            is_active=True,
        )
        db_session.add(emp)
        db_session.commit()
        db_session.refresh(emp)
        return emp

    def test_create_group_sessions_have_group_level_id(self, db_session):
        """T011-INT-01: Create group → sessions have group_level_id."""
        from tests.utils.db_helpers import create_test_course
        course = create_test_course(db_session, name=_unique("T011-INT01"))
        emp = self._create_employee(db_session)

        inp = CreateGroupWithLevelDTO(
            group_input=ScheduleGroupInput(
                course_id=course.id,
                instructor_id=emp.id,
                schedule={"day": "Sunday", "time_start": "13:00", "time_end": "14:00"},
            ),
            start_date=date.today(),
        )
        lifecycle = GroupLifecycleService()
        result = lifecycle.create_group_with_first_level(inp)

        assert result.sessions_count > 0
        stmt = select(CourseSession).where(CourseSession.group_id == result.group_id)
        sessions = db_session.exec(stmt).all()
        for s in sessions:
            assert s.group_level_id is not None

    def test_progress_level_sessions_have_new_group_level_id(self, db_session):
        """Progress level → new sessions have new group_level_id."""
        from tests.utils.db_helpers import create_test_course
        course = create_test_course(db_session, name=_unique("T011-INT-01b"))
        emp = self._create_employee(db_session)

        inp = CreateGroupWithLevelDTO(
            group_input=ScheduleGroupInput(
                course_id=course.id,
                instructor_id=emp.id,
                schedule={"day": "Sunday", "time_start": "13:00", "time_end": "14:00"},
            ),
            start_date=date.today(),
        )
        lifecycle = GroupLifecycleService()
        result = lifecycle.create_group_with_first_level(inp)

        from datetime import timedelta
        progress = ProgressLevelDTO(
            group_id=result.group_id, target_level=2,
            complete_current_level=True,
            session_start_date=date.today() + timedelta(days=30),
        )
        prog_result = lifecycle.progress_to_next_level(progress)

        stmt = select(CourseSession).where(
            CourseSession.group_id == result.group_id,
            CourseSession.level_number == 2,
        )
        sessions = db_session.exec(stmt).all()
        assert len(sessions) > 0
        for s in sessions:
            assert s.group_level_id is not None
            assert s.group_level_id != result.level_id
