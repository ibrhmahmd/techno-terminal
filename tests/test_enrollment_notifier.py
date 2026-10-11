"""EnrollmentNotifier port wiring and behaviour (ADR-0007, ticket #19)."""

from app.db.uow import unit_of_work
from app.modules.crm import StudentActivityService
from app.modules.enrollments import EnrollmentNotifier
from app.modules.enrollments.api.deps import get_enrollment_notifier as enrollments_deps_get_notifier
from app.modules.enrollments.schemas.enrollment_schemas import EnrollStudentInput
from app.modules.enrollments.services.enrollment_service import EnrollmentService
from app.modules.notifications.adapters import get_enrollment_notifier as adapters_get_notifier
from tests.test_enrollment_atomicity import _cleanup, _seed
from tests.utils.enrollment_notifier_fake import FakeEnrollmentNotifier


def test_fake_satisfies_the_port():
    notifier: EnrollmentNotifier = FakeEnrollmentNotifier()
    notifier.enrollment_created(student_id=1, enrollment_id=2, group_id=3, level_number=1)
    assert notifier.calls == [
        ("enrollment_created", {"student_id": 1, "enrollment_id": 2, "group_id": 3, "level_number": 1})
    ]


def test_create_app_overrides_the_notifier_with_the_adapter():
    from app.api.main import create_app

    app = create_app()
    assert app.dependency_overrides[enrollments_deps_get_notifier] is adapters_get_notifier


def test_enroll_student_notifies_after_commit():
    course_id, group_id, student_id = _seed()
    fake = FakeEnrollmentNotifier()
    try:
        with unit_of_work() as uow:
            svc = EnrollmentService(uow, activity_svc=StudentActivityService(uow), notifier=fake)
            result = svc.enroll_student(EnrollStudentInput(student_id=student_id, group_id=group_id))
        assert len(fake.calls) == 1
        name, kwargs = fake.calls[0]
        assert name == "enrollment_created"
        assert kwargs["student_id"] == student_id
        assert kwargs["enrollment_id"] == result.enrollment.id
        assert kwargs["group_id"] == group_id
    finally:
        _cleanup(course_id, group_id, student_id)


def test_notifier_failure_never_fails_the_use_case():
    course_id, group_id, student_id = _seed()
    fake = FakeEnrollmentNotifier(should_raise=True)
    try:
        with unit_of_work() as uow:
            svc = EnrollmentService(uow, activity_svc=StudentActivityService(uow), notifier=fake)
            result = svc.enroll_student(EnrollStudentInput(student_id=student_id, group_id=group_id))
        assert result.enrollment.id is not None
    finally:
        _cleanup(course_id, group_id, student_id)
