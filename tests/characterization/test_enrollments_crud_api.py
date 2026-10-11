"""Characterization tests for the Enrollments CRUD HTTP API (ticket #19).

Pins the exact status codes, response envelopes and field shapes of the three
write endpoints under ``/api/v1/enrollments`` served by
``app/api/routers/enrollments_router.py`` BEFORE the Enrollments HTTP layer
moves into ``app/modules/enrollments/api/``:

    POST   /enrollments
    PATCH  /enrollments/{enrollment_id}
    DELETE /enrollments/{enrollment_id}

Buckets
-------
* All three routes are writes. ``enroll_student`` opens its own
  ``unit_of_work()``; ``update_enrollment`` / ``drop_enrollment`` open their own
  ``get_session()``. Every test seeds the student/group/course/enrollment rows
  through the committed ``db_session`` fixture (uuid-tagged) so the services'
  own sessions can see them, and their writes REALLY COMMIT.
* Enrollment writes schedule notification background tasks. The
  ``noop_notifications`` fixture overrides the notifier port providers with an
  in-memory no-op so no real mail/SMS dispatch (Gmail/Twilio) can run.

Pinned quirks (pinned, not endorsed)
------------------------------------
* POST/PATCH/DELETE responses carry ``group_name``/``course_name``/
  ``instructor_name`` as ``null`` even though the group/course exist: the
  service validates ``EnrollmentDTO`` straight off the ORM row and never
  hydrates those display fields.
* POST over capacity still returns 201 and enrolls; the only signal is the
  appended message suffix ``WARNING: Group capacity exceeded.``
* An inactive student or non-active group is a 409 ``BusinessRuleError``,
  not a 422/404.
* PATCH on a ``dropped``/``transferred`` enrollment is a 409.

Run
---
GMAIL_SENDER_ADDRESS= GMAIL_APP_PASSWORD= TWILIO_ACCOUNT_SID= TWILIO_AUTH_TOKEN= SUPABASE_URL=http://127.0.0.1:9 /home/ibrahim/Desktop/techno-projects/techno-terminal/.venv/bin/python -m pytest tests/characterization/test_enrollments_crud_api.py -q -p no:cacheprovider
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
    from tests.utils.noop_notifiers import noop_notifiers

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


# ── POST /enrollments ─────────────────────────────────────────────────────────


def test_enroll_student(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """POST /enrollments enrolls an active student and returns 201."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id, level_number=2)
    student = _make_student(db_session, status="active")

    r = client_with_uow.post(
        "/api/v1/enrollments",
        headers=mock_admin_headers,
        json={
            "student_id": student.id,
            "group_id": group.id,
            "amount_due": 750.0,
            "discount": 25.5,
            "notes": "first level",
        },
    )

    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Student enrolled successfully."
    data = body["data"]
    assert set(data) == _ENROLLMENT_FIELDS
    assert isinstance(data["id"], int)
    assert data["student_id"] == student.id
    assert data["group_id"] == group.id
    assert data["level_number"] == 2
    assert data["status"] == "active"
    assert data["amount_due"] == 750.0
    assert data["discount_applied"] == 25.5
    assert data["notes"] == "first level"
    # current behaviour (pinned, not endorsed): display names are not hydrated.
    assert data["group_name"] is None
    assert data["course_name"] is None
    assert data["instructor_name"] is None
    assert data["payment_status"] is None
    assert data["amount_remaining"] is None
    assert isinstance(data["enrolled_at"], str)


def test_enroll_student_unknown_student(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """POST /enrollments with an unknown student id returns 404."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)

    r = client_with_uow.post(
        "/api/v1/enrollments",
        headers=mock_admin_headers,
        json={"student_id": 999999999, "group_id": group.id},
    )

    assert r.status_code == 404
    body = r.json()
    assert set(body) == {"success", "error", "message"}
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert body["message"] == "Student ID 999999999 not found."


def test_enroll_student_unknown_group(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """POST /enrollments with an unknown group id returns 404."""
    student = _make_student(db_session, status="active")

    r = client_with_uow.post(
        "/api/v1/enrollments",
        headers=mock_admin_headers,
        json={"student_id": student.id, "group_id": 999999999},
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    # current behaviour (pinned, not endorsed): the message comes from
    # GroupCoreService, not the router's own f-string.
    assert body["message"] == "Group 999999999 not found."


def test_enroll_student_inactive_student(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """POST /enrollments for an inactive student returns 409."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    student = _make_student(db_session, full_name="Inactive Kid", status="inactive")

    r = client_with_uow.post(
        "/api/v1/enrollments",
        headers=mock_admin_headers,
        json={"student_id": student.id, "group_id": group.id},
    )

    assert r.status_code == 409
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "BusinessRuleError"
    assert body["message"] == "Student 'Inactive Kid' is inactive and cannot be enrolled."


def test_enroll_student_inactive_group(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """POST /enrollments into a non-active group returns 409."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id, name="Frozen Group", status="completed")
    student = _make_student(db_session, status="active")

    r = client_with_uow.post(
        "/api/v1/enrollments",
        headers=mock_admin_headers,
        json={"student_id": student.id, "group_id": group.id},
    )

    assert r.status_code == 409
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "BusinessRuleError"
    assert body["message"] == "Group 'Frozen Group' is not active (status: completed)."


def test_enroll_student_duplicate(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """POST /enrollments twice for the same student+group returns 409."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    student = _make_student(db_session, full_name="Dup Kid", status="active")
    payload = {"student_id": student.id, "group_id": group.id}

    first = client_with_uow.post(
        "/api/v1/enrollments", headers=mock_admin_headers, json=payload
    )
    assert first.status_code == 201
    enrollment_id = first.json()["data"]["id"]

    second = client_with_uow.post(
        "/api/v1/enrollments", headers=mock_admin_headers, json=payload
    )

    assert second.status_code == 409
    body = second.json()
    assert body["success"] is False
    assert body["error"] == "ConflictError"
    assert body["message"] == (
        f"'Dup Kid' is already enrolled in this group (Enrollment ID: {enrollment_id})."
    )


def test_enroll_student_capacity_exceeded_still_201(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """POST /enrollments over capacity enrolls anyway; message gains a warning.

    current behaviour (pinned, not endorsed): capacity is a warning, not a block.
    """
    course = _make_course(db_session)
    group = _make_group(db_session, course.id, max_capacity=1)
    seated = _make_student(db_session, status="active")
    _make_enrollment(db_session, seated.id, group.id, status="active")
    newcomer = _make_student(db_session, status="active")

    r = client_with_uow.post(
        "/api/v1/enrollments",
        headers=mock_admin_headers,
        json={"student_id": newcomer.id, "group_id": group.id},
    )

    assert r.status_code == 201
    body = r.json()
    assert body["success"] is True
    assert body["message"] == (
        "Student enrolled successfully. WARNING: Group capacity exceeded."
    )
    assert body["data"]["status"] == "active"


def test_enroll_student_validation_error(client_with_uow, override_auth, mock_admin_headers):
    """POST /enrollments without required fields returns 422."""
    r = client_with_uow.post(
        "/api/v1/enrollments", headers=mock_admin_headers, json={}
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


# ── PATCH /enrollments/{enrollment_id} ────────────────────────────────────────


def test_update_enrollment(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """PATCH /enrollments/{id} updates amount_due and notes."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    student = _make_student(db_session, status="active")
    enrollment = _make_enrollment(
        db_session, student.id, group.id, amount_due=500.0, notes="old"
    )

    r = client_with_uow.patch(
        f"/api/v1/enrollments/{enrollment.id}",
        headers=mock_admin_headers,
        json={"amount_due": 250.0, "notes": "new note"},
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Enrollment updated successfully."
    data = body["data"]
    assert set(data) == _ENROLLMENT_FIELDS
    assert data["id"] == enrollment.id
    assert data["amount_due"] == 250.0
    assert data["notes"] == "new note"
    assert data["status"] == "active"
    # current behaviour (pinned, not endorsed): display names are not hydrated.
    assert data["group_name"] is None
    assert data["course_name"] is None
    assert data["instructor_name"] is None


def test_update_enrollment_empty_body(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """PATCH /enrollments/{id} with no editable fields returns the row unchanged."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    student = _make_student(db_session, status="active")
    enrollment = _make_enrollment(db_session, student.id, group.id, amount_due=500.0)

    r = client_with_uow.patch(
        f"/api/v1/enrollments/{enrollment.id}",
        headers=mock_admin_headers,
        json={},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["message"] == "Enrollment updated successfully."
    assert body["data"]["id"] == enrollment.id
    assert body["data"]["amount_due"] == 500.0


def test_update_enrollment_not_found(client_with_uow, override_auth, mock_admin_headers):
    """PATCH /enrollments/999999999 returns 404."""
    r = client_with_uow.patch(
        "/api/v1/enrollments/999999999",
        headers=mock_admin_headers,
        json={"amount_due": 10.0},
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert body["message"] == "Enrollment 999999999 not found."


def test_update_enrollment_negative_amount(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """PATCH /enrollments/{id} with a negative amount_due returns 409."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    student = _make_student(db_session, status="active")
    enrollment = _make_enrollment(db_session, student.id, group.id)

    r = client_with_uow.patch(
        f"/api/v1/enrollments/{enrollment.id}",
        headers=mock_admin_headers,
        json={"amount_due": -5.0},
    )

    assert r.status_code == 409
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "BusinessRuleError"
    assert body["message"] == "Amount due cannot be negative."


def test_update_enrollment_negative_discount(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """PATCH /enrollments/{id} with a negative discount_applied returns 409."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    student = _make_student(db_session, status="active")
    enrollment = _make_enrollment(db_session, student.id, group.id)

    r = client_with_uow.patch(
        f"/api/v1/enrollments/{enrollment.id}",
        headers=mock_admin_headers,
        json={"discount_applied": -1.0},
    )

    assert r.status_code == 409
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "BusinessRuleError"
    assert body["message"] == "Discount applied cannot be negative."


def test_update_dropped_enrollment(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """PATCH /enrollments/{id} on a dropped enrollment returns 409."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    student = _make_student(db_session, status="active")
    enrollment = _make_enrollment(db_session, student.id, group.id, status="dropped")

    r = client_with_uow.patch(
        f"/api/v1/enrollments/{enrollment.id}",
        headers=mock_admin_headers,
        json={"amount_due": 100.0},
    )

    assert r.status_code == 409
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "BusinessRuleError"
    assert body["message"] == "Cannot edit dropped or transferred enrollments."


# ── DELETE /enrollments/{enrollment_id} ───────────────────────────────────────


def test_drop_enrollment(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """DELETE /enrollments/{id} set status 'dropped' (not a hard delete)."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    student = _make_student(db_session, status="active")
    enrollment = _make_enrollment(db_session, student.id, group.id, status="active")

    r = client_with_uow.delete(
        f"/api/v1/enrollments/{enrollment.id}",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Enrollment dropped successfully."
    data = body["data"]
    assert set(data) == _ENROLLMENT_FIELDS
    assert data["id"] == enrollment.id
    assert data["status"] == "dropped"


def test_drop_enrollment_with_reason(
    client_with_uow, override_auth, mock_admin_headers, db_session, noop_notifications
):
    """DELETE /enrollments/{id}?reason=... still returns 200 and drops."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    student = _make_student(db_session, status="active")
    enrollment = _make_enrollment(db_session, student.id, group.id, status="active")

    r = client_with_uow.delete(
        f"/api/v1/enrollments/{enrollment.id}?reason=moved+away",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["message"] == "Enrollment dropped successfully."
    assert body["data"]["status"] == "dropped"


def test_drop_enrollment_not_found(client_with_uow, override_auth, mock_admin_headers):
    """DELETE /enrollments/999999999 returns 404."""
    r = client_with_uow.delete(
        "/api/v1/enrollments/999999999",
        headers=mock_admin_headers,
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert body["message"] == "Enrollment 999999999 not found."


# ── Auth ──────────────────────────────────────────────────────────────────────


def test_enrollments_crud_endpoints_require_auth(client):
    """All three endpoints without auth return 401."""
    assert client.post("/api/v1/enrollments", json={}).status_code == 401
    assert client.patch(
        "/api/v1/enrollments/1", json={"amount_due": 1.0}
    ).status_code == 401
    assert client.delete("/api/v1/enrollments/1").status_code == 401
