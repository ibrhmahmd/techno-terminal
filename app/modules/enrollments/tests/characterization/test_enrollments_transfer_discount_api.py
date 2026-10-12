"""Characterization tests for the Enrollments transfer/discount HTTP API (ticket #19).

Pins the exact status codes, response envelopes and field shapes of two write
endpoints under ``/api/v1/enrollments`` served by
``app/api/routers/enrollments_router.py`` BEFORE the Enrollments HTTP layer
moves into ``app/modules/enrollments/api/``:

    POST   /enrollments/transfer
    POST   /enrollments/{enrollment_id}/discount

Buckets
-------
* Both routes are writes. ``transfer_student`` and ``apply_sibling_discount``
  open their own ``get_session()``. Every test seeds the student/group/course/
  enrollment rows through the committed ``db_session`` fixture (uuid-tagged) so
  the services' own sessions can see them, and their writes REALLY COMMIT.
* Transfer schedules a notification background task. The ``noop_notifications``
  fixture overrides the notifier port providers with an in-memory no-op so no
  real mail/SMS dispatch (Gmail/Twilio) can run. The discount route passes no
  ``background_tasks``, so it never notifies.

Pinned quirks (pinned, not endorsed)
-----------------------------------
* Transfer checks the target group BEFORE the source enrollment: an inactive
  target group wins even when the source id does not exist.
* The transfer response carries ``group_name``/``course_name``/
  ``instructor_name`` as ``null``: the service validates ``EnrollmentDTO``
  straight off the ORM row and never hydrates those display fields.
* Applying a discount SETS ``discount_applied`` to the requested amount; the
  router docstring says "added to existing", but the repository overwrites.
* Discount on a non-active enrollment is a 409 ``BusinessRuleError``.

Run
---
GMAIL_SENDER_ADDRESS= GMAIL_APP_PASSWORD= TWILIO_ACCOUNT_SID= TWILIO_AUTH_TOKEN= SUPABASE_URL=http://127.0.0.1:9 /home/ibrahim/Desktop/techno-projects/techno-terminal/.venv/bin/python -m pytest app/modules/enrollments/tests/characterization/test_enrollments_transfer_discount_api.py -q -p no:cacheprovider
"""

import uuid
from datetime import date, time

import pytest

from app.modules.academics.models.course_models import Course
from app.modules.academics.models.group_models import Group
from app.modules.crm.models.student_models import Student
from app.modules.enrollments.models.enrollment_models import Enrollment

_ENROLLMENT_FIELDS = {
    "id",
    "student_id",
    "group_id",
    "group_name",
    "course_name",
    "instructor_name",
    "level_number",
    "status",
    "amount_due",
    "discount_applied",
    "payment_status",
    "amount_remaining",
    "notes",
    "enrolled_at",
}


def _short() -> str:
    return uuid.uuid4().hex[:10]


@pytest.fixture
def noop_notifications(app):
    """Replace every notifier port provider with a no-op so nothing can be dispatched."""
    from app.testing.noop_notifiers import noop_notifiers

    with noop_notifiers(app) as stub:
        yield stub


def _make_course(db_session, **overrides) -> Course:
    course = Course(
        name=overrides.pop("name", f"Course {_short()}"),
        category=overrides.pop("category", "software"),
        description=overrides.pop("description", None),
        notes=overrides.pop("notes", None),
        price_per_level=overrides.pop("price_per_level", 1000.0),
        sessions_per_level=overrides.pop("sessions_per_level", 8),
        is_active=overrides.pop("is_active", True),
        **overrides,
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    return course


def _make_group(db_session, course_id: int, **overrides) -> Group:
    group = Group(
        name=overrides.pop("name", f"Group {_short()}"),
        course_id=course_id,
        instructor_id=overrides.pop("instructor_id", None),
        level_number=overrides.pop("level_number", 1),
        max_capacity=overrides.pop("max_capacity", 15),
        default_day=overrides.pop("default_day", "Saturday"),
        default_time_start=overrides.pop("default_time_start", time(14, 0)),
        default_time_end=overrides.pop("default_time_end", time(16, 0)),
        status=overrides.pop("status", "active"),
        **overrides,
    )
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


def _make_student(db_session, **overrides) -> Student:
    student = Student(
        full_name=overrides.pop("full_name", f"Student {_short()}"),
        date_of_birth=overrides.pop("date_of_birth", None),
        gender=overrides.pop("gender", None),
        phone=overrides.pop("phone", f"555{_short()[:7]}"),
        status=overrides.pop("status", "active"),
        **overrides,
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student


def _make_enrollment(db_session, student_id: int, group_id: int, **overrides) -> Enrollment:
    enrollment = Enrollment(
        student_id=student_id,
        group_id=group_id,
        level_number=overrides.pop("level_number", 1),
        amount_due=overrides.pop("amount_due", None),
        discount_applied=overrides.pop("discount_applied", 0.0),
        status=overrides.pop("status", "active"),
        notes=overrides.pop("notes", None),
        enrolled_at=overrides.pop("enrolled_at", date(2024, 3, 1)),
        **overrides,
    )
    db_session.add(enrollment)
    db_session.commit()
    db_session.refresh(enrollment)
    return enrollment


# ── POST /enrollments/transfer ────────────────────────────────────────────────


def test_transfer_student(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """POST /enrollments/transfer moves an active enrollment to a new group."""
    course = _make_course(db_session)
    source_group = _make_group(db_session, course.id, level_number=1)
    target_group = _make_group(db_session, course.id, level_number=3, name="Target Group")
    student = _make_student(db_session, status="active")
    source = _make_enrollment(
        db_session, student.id, source_group.id, amount_due=800.0, discount_applied=30.0
    )

    r = client_with_uow.post(
        "/api/v1/enrollments/transfer",
        headers=mock_admin_headers,
        json={"from_enrollment_id": source.id, "to_group_id": target_group.id},
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Student transferred successfully."
    data = body["data"]
    assert set(data) == _ENROLLMENT_FIELDS
    assert isinstance(data["id"], int)
    assert data["id"] != source.id
    assert data["student_id"] == student.id
    assert data["group_id"] == target_group.id
    assert data["level_number"] == 3
    assert data["status"] == "active"
    assert data["amount_due"] == 800.0
    assert data["discount_applied"] == 30.0
    # current behaviour (pinned, not endorsed): display names are not hydrated.
    assert data["group_name"] is None
    assert data["course_name"] is None
    assert data["instructor_name"] is None
    assert data["payment_status"] is None
    assert data["amount_remaining"] is None
    assert isinstance(data["enrolled_at"], str)


def test_transfer_marks_source_transferred(
    client_with_uow, override_auth, mock_admin_headers, db_session, uow, noop_notifications
):
    """POST /enrollments/transfer sets the OLD enrollment status to 'transferred'."""
    course = _make_course(db_session)
    source_group = _make_group(db_session, course.id)
    target_group = _make_group(db_session, course.id)
    student = _make_student(db_session, status="active")
    source = _make_enrollment(db_session, student.id, source_group.id, status="active")

    r = client_with_uow.post(
        "/api/v1/enrollments/transfer",
        headers=mock_admin_headers,
        json={"from_enrollment_id": source.id, "to_group_id": target_group.id},
    )
    assert r.status_code == 200

    # The use case now commits through the injected UnitOfWork (a savepoint of
    # the uow fixture's transaction), so read the result through that same session.
    assert uow.session.get(Enrollment, source.id).status == "transferred"


def test_transfer_target_group_not_active(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """POST /enrollments/transfer into a non-active target group returns 409.

    current behaviour (pinned, not endorsed): the target group is validated
    before the source enrollment, so this wins even for a valid source.
    """
    course = _make_course(db_session)
    source_group = _make_group(db_session, course.id)
    target_group = _make_group(db_session, course.id, name="Frozen Target", status="completed")
    student = _make_student(db_session, status="active")
    source = _make_enrollment(db_session, student.id, source_group.id, status="active")

    r = client_with_uow.post(
        "/api/v1/enrollments/transfer",
        headers=mock_admin_headers,
        json={"from_enrollment_id": source.id, "to_group_id": target_group.id},
    )

    assert r.status_code == 409
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "BusinessRuleError"
    assert body["message"] == "Target group 'Frozen Target' is not active."


def test_transfer_source_not_found(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """POST /enrollments/transfer with an unknown source enrollment returns 404."""
    course = _make_course(db_session)
    target_group = _make_group(db_session, course.id)

    r = client_with_uow.post(
        "/api/v1/enrollments/transfer",
        headers=mock_admin_headers,
        json={"from_enrollment_id": 999999999, "to_group_id": target_group.id},
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert body["message"] == "Source enrollment 999999999 not found."


def test_transfer_source_not_active(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """POST /enrollments/transfer of a dropped enrollment returns 409."""
    course = _make_course(db_session)
    source_group = _make_group(db_session, course.id)
    target_group = _make_group(db_session, course.id)
    student = _make_student(db_session, status="active")
    source = _make_enrollment(db_session, student.id, source_group.id, status="dropped")

    r = client_with_uow.post(
        "/api/v1/enrollments/transfer",
        headers=mock_admin_headers,
        json={"from_enrollment_id": source.id, "to_group_id": target_group.id},
    )

    assert r.status_code == 409
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "BusinessRuleError"
    assert body["message"] == "Can only transfer an active enrollment."


def test_transfer_unknown_target_group(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """POST /enrollments/transfer to an unknown group returns 404 from GroupCoreService."""
    course = _make_course(db_session)
    source_group = _make_group(db_session, course.id)
    student = _make_student(db_session, status="active")
    source = _make_enrollment(db_session, student.id, source_group.id, status="active")

    r = client_with_uow.post(
        "/api/v1/enrollments/transfer",
        headers=mock_admin_headers,
        json={"from_enrollment_id": source.id, "to_group_id": 999999999},
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert body["message"] == "Group 999999999 not found."


def test_transfer_validation_error(client_with_uow, override_auth, mock_admin_headers):
    """POST /enrollments/transfer without required fields returns 422."""
    r = client_with_uow.post(
        "/api/v1/enrollments/transfer", headers=mock_admin_headers, json={}
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


# ── POST /enrollments/{enrollment_id}/discount ────────────────────────────────


def test_apply_sibling_discount_default(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """POST /enrollments/{id}/discount defaults to 50.0 and overwrites the field."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    student = _make_student(db_session, status="active")
    enrollment = _make_enrollment(
        db_session, student.id, group.id, discount_applied=30.0, status="active"
    )

    r = client_with_uow.post(
        f"/api/v1/enrollments/{enrollment.id}/discount",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Discount of 50.0 applied successfully."
    data = body["data"]
    assert set(data) == _ENROLLMENT_FIELDS
    assert data["id"] == enrollment.id
    # current behaviour (pinned, not endorsed): SET, not added to the prior 30.0.
    assert data["discount_applied"] == 50.0
    assert data["status"] == "active"
    # current behaviour (pinned, not endorsed): display names are not hydrated.
    assert data["group_name"] is None
    assert data["course_name"] is None
    assert data["instructor_name"] is None


def test_apply_sibling_discount_custom_amount(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """POST /enrollments/{id}/discount?discount_amount=25 sets discount to 25.0."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    student = _make_student(db_session, status="active")
    enrollment = _make_enrollment(db_session, student.id, group.id, status="active")

    r = client_with_uow.post(
        f"/api/v1/enrollments/{enrollment.id}/discount?discount_amount=25",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["message"] == "Discount of 25.0 applied successfully."
    assert body["data"]["discount_applied"] == 25.0


def test_apply_sibling_discount_not_found(
    client_with_uow, override_auth, mock_admin_headers, noop_notifications
):
    """POST /enrollments/999999999/discount returns 404."""
    r = client_with_uow.post(
        "/api/v1/enrollments/999999999/discount",
        headers=mock_admin_headers,
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert body["message"] == "Enrollment 999999999 not found."


def test_apply_sibling_discount_not_active(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """POST /enrollments/{id}/discount on a dropped enrollment returns 409."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    student = _make_student(db_session, status="active")
    enrollment = _make_enrollment(db_session, student.id, group.id, status="dropped")

    r = client_with_uow.post(
        f"/api/v1/enrollments/{enrollment.id}/discount",
        headers=mock_admin_headers,
    )

    assert r.status_code == 409
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "BusinessRuleError"
    assert body["message"] == "Can only apply discount to active enrollments."


def test_apply_sibling_discount_invalid_amount(
    client_with_uow, override_auth, mock_admin_headers
):
    """POST /enrollments/{id}/discount with a non-numeric amount returns 422."""
    r = client_with_uow.post(
        "/api/v1/enrollments/1/discount?discount_amount=abc",
        headers=mock_admin_headers,
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


# ── Auth ──────────────────────────────────────────────────────────────────────


def test_transfer_and_discount_require_auth(client):
    """Both endpoints without auth return 401."""
    assert client.post(
        "/api/v1/enrollments/transfer",
        json={"from_enrollment_id": 1, "to_group_id": 1},
    ).status_code == 401
    assert client.post("/api/v1/enrollments/1/discount").status_code == 401
