"""Atomicity of ``enroll_student`` under ADR-0001 (ticket #19, phase B1).

After the Unit-of-Work conversion, ``EnrollmentService.enroll_student`` writes
the enrollment row AND its CRM activity log over one injected ``UnitOfWork`` and
commits exactly once. This file proves that:

* a failure *after* the activity log is written rolls back BOTH rows;
* a success persists BOTH rows;
* the whole use case checks out exactly one connection from the engine pool.

Seeding uses committed, uuid-tagged rows and a real ``UnitOfWork`` over a real
session (``unit_of_work()``), not the savepoint ``uow`` fixture, so a real
commit/rollback is exercised. Everything created is deleted in teardown so the
file is rerunnable.

Run
---
GMAIL_SENDER_ADDRESS= GMAIL_APP_PASSWORD= TWILIO_ACCOUNT_SID= TWILIO_AUTH_TOKEN= \
SUPABASE_URL=http://127.0.0.1:9 /home/ibrahim/Desktop/techno-projects/techno-terminal/.venv/bin/python \
-m pytest tests/test_enrollment_atomicity.py -q -p no:cacheprovider
"""

import threading
import uuid
from datetime import time

import pytest
from sqlalchemy import event
from sqlmodel import delete, select

from app.db.connection import get_engine, get_session
from app.db.uow import unit_of_work
from app.modules.academics.models.course_models import Course
from app.modules.academics.models.group_models import Group
from app.modules.crm import StudentActivityService
from app.modules.crm.models.activity_models import StudentActivityLog
from app.modules.crm.models.student_models import Student
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.enrollments.schemas.enrollment_schemas import EnrollStudentInput
from app.modules.enrollments.services.enrollment_service import EnrollmentService


def _short() -> str:
    return uuid.uuid4().hex[:10]


def _seed() -> tuple[int, int, int]:
    """Commit a course + active group + active student, uuid-tagged."""
    with get_session() as session:
        course = Course(
            name=f"AtomicCourse-{_short()}",
            category="software",
            price_per_level=1000.0,
            sessions_per_level=8,
            is_active=True,
        )
        session.add(course)
        session.commit()
        session.refresh(course)

        group = Group(
            name=f"AtomicGroup-{_short()}",
            course_id=course.id,
            level_number=1,
            max_capacity=15,
            default_day="Saturday",
            default_time_start=time(14, 0),
            default_time_end=time(16, 0),
            status="active",
        )
        session.add(group)
        session.commit()
        session.refresh(group)

        student = Student(
            full_name=f"Atomic Student {_short()}",
            phone=f"555{_short()[:7]}",
            status="active",
        )
        session.add(student)
        session.commit()
        session.refresh(student)

        return course.id, group.id, student.id


def _cleanup(course_id: int, group_id: int, student_id: int) -> None:
    with get_session() as session:
        session.exec(
            delete(StudentActivityLog).where(
                StudentActivityLog.student_id == student_id
            )
        )
        session.exec(delete(Enrollment).where(Enrollment.student_id == student_id))
        session.exec(delete(Student).where(Student.id == student_id))
        session.exec(delete(Group).where(Group.id == group_id))
        session.exec(delete(Course).where(Course.id == course_id))
        session.commit()


def test_failure_after_activity_log_rolls_back_both(monkeypatch):
    """A raise after the activity log write must roll back enrollment + log."""
    course_id, group_id, student_id = _seed()
    try:
        original_log_enrollment = StudentActivityService.log_enrollment

        def _explode_after_log(self, dto):
            original_log_enrollment(self, dto)
            raise RuntimeError("boom after activity log")

        monkeypatch.setattr(
            StudentActivityService, "log_enrollment", _explode_after_log
        )

        with pytest.raises(RuntimeError, match="boom after activity log"):
            with unit_of_work() as uow:
                svc = EnrollmentService(
                    uow, activity_svc=StudentActivityService(uow)
                )
                svc.enroll_student(
                    EnrollStudentInput(
                        student_id=student_id, group_id=group_id, amount_due=100.0
                    )
                )

        with get_session() as session:
            enrollment = session.exec(
                select(Enrollment).where(Enrollment.student_id == student_id)
            ).first()
            assert enrollment is None
            activity = session.exec(
                select(StudentActivityLog).where(
                    StudentActivityLog.student_id == student_id
                )
            ).first()
            assert activity is None
    finally:
        _cleanup(course_id, group_id, student_id)


def test_success_persists_enrollment_and_activity_log():
    """A successful enroll commits both the enrollment and its activity log."""
    course_id, group_id, student_id = _seed()
    try:
        with unit_of_work() as uow:
            svc = EnrollmentService(uow, activity_svc=StudentActivityService(uow))
            result = svc.enroll_student(
                EnrollStudentInput(
                    student_id=student_id, group_id=group_id, amount_due=250.0
                )
            )

        with get_session() as session:
            enrollment = session.exec(
                select(Enrollment).where(
                    Enrollment.student_id == student_id,
                    Enrollment.group_id == group_id,
                )
            ).one()
            assert enrollment.id == result.enrollment.id

            activity = session.exec(
                select(StudentActivityLog).where(
                    StudentActivityLog.student_id == student_id,
                    StudentActivityLog.activity_type == "enrollment",
                )
            ).first()
            assert activity is not None
            assert activity.reference_id == enrollment.id
    finally:
        _cleanup(course_id, group_id, student_id)


def test_enroll_student_checks_out_exactly_one_connection():
    """The whole use case must use a single connection from the pool."""
    course_id, group_id, student_id = _seed()
    engine = get_engine()
    open_count = 0
    max_open = 0

    this_thread = threading.get_ident()

    def _on_checkout(dbapi_connection, connection_record, connection_proxy):
        # Background threads (app lifespan metrics collector started by other
        # tests) also check out connections; only count this thread's.
        if threading.get_ident() != this_thread:
            return
        nonlocal open_count, max_open
        open_count += 1
        max_open = max(max_open, open_count)

    def _on_checkin(dbapi_connection, connection_record):
        nonlocal open_count
        if threading.get_ident() != this_thread:
            return
        open_count -= 1

    event.listen(engine, "checkout", _on_checkout)
    event.listen(engine, "checkin", _on_checkin)
    try:
        with unit_of_work() as uow:
            svc = EnrollmentService(uow, activity_svc=StudentActivityService(uow))
            svc.enroll_student(
                EnrollStudentInput(student_id=student_id, group_id=group_id)
            )
    finally:
        event.remove(engine, "checkout", _on_checkout)
        event.remove(engine, "checkin", _on_checkin)
        _cleanup(course_id, group_id, student_id)

    # Never more than one connection checked out at a time (the old code held up
    # to five sessions); after commit the session may re-acquire a pooled one.
    assert max_open == 1
