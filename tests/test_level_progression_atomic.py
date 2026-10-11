"""Atomicity of group level progression + enrollment migration (ticket #32).

`EnrollmentLifecycleService.progress_group_level` asks academics (via its
facade) to create the next level and its sessions, then migrates the active
enrollments — all in one `get_session()` transaction that commits once. This
test proves the two steps share that transaction:

* If the enrollment-migration step raises, the new level and its sessions must
  be rolled back (not persisted), and the current level must stay active.
* On success, both the new level and its sessions are persisted.

Seeding uses committed, uuid-tagged rows (the legacy services open their own
sessions, so rollback-only fixtures are invisible to them). Everything created
is deleted in teardown so the file is rerunnable.

Run
---
GMAIL_SENDER_ADDRESS= GMAIL_APP_PASSWORD= TWILIO_ACCOUNT_SID= TWILIO_AUTH_TOKEN= \
SUPABASE_URL=http://127.0.0.1:9 /home/ibrahim/Desktop/techno-projects/techno-terminal/.venv/bin/python \
-m pytest tests/test_level_progression_atomic.py -q -p no:cacheprovider
"""

import uuid

import pytest
from sqlmodel import delete, select

from app.db.connection import get_session
from app.db.uow import UnitOfWork
from app.modules.academics import ProgressLevelDTO
from app.modules.academics.models import Group, CourseSession
from app.modules.academics.models.course_models import Course
from app.modules.academics.models.group_level_models import (
    GroupLevel,
    GroupCourseHistory,
)
from app.modules.enrollments.services.enrollment_lifecycle_service import EnrollmentLifecycleService
from tests.utils.db_helpers import (
    create_test_course,
    create_test_group,
    create_test_group_level,
)


def _short() -> str:
    return uuid.uuid4().hex[:10]


def _cleanup(course_id: int, group_id: int) -> None:
    with get_session() as session:
        session.exec(delete(CourseSession).where(CourseSession.group_id == group_id))
        session.exec(delete(GroupLevel).where(GroupLevel.group_id == group_id))
        session.exec(
            delete(GroupCourseHistory).where(GroupCourseHistory.group_id == group_id)
        )
        session.exec(delete(Group).where(Group.id == group_id))
        session.exec(delete(Course).where(Course.id == course_id))
        session.commit()


@pytest.fixture
def group_with_level_one(db_session):
    """Committed course + active group + active level 1 (no sessions seeded)."""
    course = create_test_course(
        db_session, name=f"AtomicCourse-{_short()}", sessions_per_level=3
    )
    group = create_test_group(
        db_session,
        course_id=course.id,
        name=f"AtomicGroup-{_short()}",
        level_number=1,
        default_day="Saturday",
    )
    create_test_group_level(
        db_session,
        group_id=group.id,
        level_number=1,
        course_id=course.id,
        status="active",
        sessions_planned=3,
    )
    yield course, group
    _cleanup(course.id, group.id)


def _progress_data(group: Group) -> ProgressLevelDTO:
    return ProgressLevelDTO(
        group_id=group.id,
        auto_migrate_enrollments=True,
        complete_current_level=True,
    )


def test_migration_failure_rolls_back_new_level_and_sessions(
    group_with_level_one, db_session, monkeypatch
):
    """A failure in the enrollment-migration step must roll back the new level."""
    _course, group = group_with_level_one

    def _boom(*args, **kwargs):
        raise RuntimeError("migration boom")

    monkeypatch.setattr(
        EnrollmentLifecycleService,
        "migrate_enrollments_to_next_level",
        _boom,
    )

    with pytest.raises(RuntimeError, match="migration boom"):
        EnrollmentLifecycleService(UnitOfWork(db_session)).progress_group_level(_progress_data(group))

    # The service was handed a bare session (no unit_of_work() context), so
    # release the aborted transaction here before another connection reads.
    db_session.rollback()

    with get_session() as session:
        levels = session.exec(
            select(GroupLevel).where(GroupLevel.group_id == group.id)
        ).all()
        assert [level.level_number for level in levels] == [1]
        assert levels[0].status == "active"

        sessions = session.exec(
            select(CourseSession).where(CourseSession.group_id == group.id)
        ).all()
        assert list(sessions) == []

        assert session.get(Group, group.id).level_number == 1


def test_success_persists_new_level_and_sessions(group_with_level_one, db_session):
    """A successful run commits both the new level and its sessions."""
    _course, group = group_with_level_one

    result = EnrollmentLifecycleService(UnitOfWork(db_session)).progress_group_level(_progress_data(group))

    assert result.old_level_number == 1
    assert result.new_level_number == 2
    assert result.sessions_created == 3
    assert result.enrollments_migrated == 0

    with get_session() as session:
        new_level = session.exec(
            select(GroupLevel).where(
                GroupLevel.group_id == group.id,
                GroupLevel.level_number == 2,
            )
        ).first()
        assert new_level is not None
        assert new_level.id == result.new_level_id

        sessions = session.exec(
            select(CourseSession).where(
                CourseSession.group_id == group.id,
                CourseSession.level_number == 2,
            )
        ).all()
        assert len(sessions) == 3

        assert session.get(Group, group.id).level_number == 2
