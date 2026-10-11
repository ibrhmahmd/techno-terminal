"""Characterization tests for the Enrollments READ HTTP API (ticket #19).

Pins the exact status codes, response envelopes and field shapes of the two
read endpoints under ``/api/v1/enrollments`` served by
``app/api/routers/enrollments_router.py`` BEFORE the Enrollments HTTP layer
moves into ``app/modules/enrollments/api/``:

    GET /enrollments/student/{student_id}
    GET /enrollments/group/{group_id}/students-summary

Buckets
-------
* Both routes are reads and resolve through ``EnrollmentDirectoryService``,
  which opens its own ``get_session()``. Every test therefore seeds the
  student/group/course/enrollment/group_level rows through the committed
  ``db_session`` fixture (uuid-tagged values) so the service's own session can
  see them. No writes happen and no notification dispatch can run — reads
  schedule no background task — so the write-path ``noop_notifications`` guard
  is unnecessary here.

Pinned quirks (pinned, not endorsed)
------------------------------------
* GET /enrollments/student/{id} for an unknown student is a 200 with an empty
  ``data`` list, not a 404. Same for an unknown group on the summary route.
* ``amount_remaining`` is computed two different ways. The student route returns
  ``max(0, -balance)`` (never negative, and always positive for an unpaid
  enrollment). The summary route returns the raw view ``balance``, which is
  ``-net_due`` (negative) for an unpaid enrollment.
* The summary route restricts to the group's *current* ``level_number`` unless
  ``?level=`` is given; ``?level=0`` is falsy and silently falls back to the
  group level.
* ``sessions_total`` is 0 when no matching ``group_levels`` row exists.
* A ``dropped`` enrollment is excluded from the summary but still returned by
  the student history route.

Run
---
GMAIL_SENDER_ADDRESS= GMAIL_APP_PASSWORD= TWILIO_ACCOUNT_SID= TWILIO_AUTH_TOKEN= SUPABASE_URL=http://127.0.0.1:9 /home/ibrahim/Desktop/techno-projects/techno-terminal/.venv/bin/python -m pytest tests/characterization/test_enrollments_reads_api.py -q -p no:cacheprovider
"""

import uuid
from datetime import date, time

from app.modules.academics.models.course_models import Course
from app.modules.academics.models.group_level_models import GroupLevel
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

_SUMMARY_FIELDS = {
    "student_id",
    "student_name",
    "enrollment_id",
    "level_number",
    "status",
    "sessions_attended",
    "sessions_total",
    "payment_status",
    "amount_remaining",
    "amount_due",
    "discount_applied",
}


def _short() -> str:
    return uuid.uuid4().hex[:10]


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


def _make_group_level(db_session, group_id: int, course_id: int, **overrides) -> GroupLevel:
    level = GroupLevel(
        group_id=group_id,
        level_number=overrides.pop("level_number", 1),
        course_id=course_id,
        instructor_id=overrides.pop("instructor_id", None),
        sessions_planned=overrides.pop("sessions_planned", 8),
        status=overrides.pop("status", "active"),
        **overrides,
    )
    db_session.add(level)
    db_session.commit()
    db_session.refresh(level)
    return level


# ── GET /enrollments/student/{student_id} ─────────────────────────────────────


def test_student_enrollments_hydrates_group_and_course(
    client_with_uow, override_auth, mock_admin_headers, db_session
):
    """Happy path: a student's enrollment is returned with hydrated names."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id, level_number=2)
    student = _make_student(db_session)
    enrollment = _make_enrollment(
        db_session,
        student.id,
        group.id,
        level_number=2,
        amount_due=1000.0,
        discount_applied=0.0,
        notes="level two",
    )

    r = client_with_uow.get(
        f"/api/v1/enrollments/student/{student.id}", headers=mock_admin_headers
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] is None
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 1

    data = body["data"][0]
    assert set(data) == _ENROLLMENT_FIELDS
    assert data["id"] == enrollment.id
    assert data["student_id"] == student.id
    assert data["group_id"] == group.id
    assert data["group_name"] == group.name
    assert data["course_name"] == course.name
    assert data["instructor_name"] is None
    assert data["level_number"] == 2
    assert data["status"] == "active"
    assert data["amount_due"] == 1000.0
    assert data["discount_applied"] == 0.0
    assert data["notes"] == "level two"
    assert data["payment_status"] == "not_paid"
    # current behaviour (pinned, not endorsed): amount_remaining = max(0, -balance),
    # so an unpaid enrollment reports the full net due as a positive number.
    assert data["amount_remaining"] == 1000.0
    assert isinstance(data["enrolled_at"], str)


def test_student_enrollments_unknown_student_returns_empty_list(
    client_with_uow, override_auth, mock_admin_headers
):
    """Unknown student id is a 200 with an empty list, not a 404."""
    r = client_with_uow.get(
        "/api/v1/enrollments/student/999999999", headers=mock_admin_headers
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["data"] == []


def test_student_enrollments_only_returns_that_student(
    client_with_uow, override_auth, mock_admin_headers, db_session
):
    """Enrollments belonging to another student are never returned."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    mine = _make_student(db_session)
    other = _make_student(db_session)
    my_enrollment = _make_enrollment(db_session, mine.id, group.id, level_number=1)
    _make_enrollment(db_session, other.id, group.id, level_number=1)

    r = client_with_uow.get(
        f"/api/v1/enrollments/student/{mine.id}", headers=mock_admin_headers
    )

    assert r.status_code == 200
    data = r.json()["data"]
    assert {row["id"] for row in data} == {my_enrollment.id}
    assert {row["student_id"] for row in data} == {mine.id}


def test_student_enrollments_requires_auth(client_with_uow, db_session):
    """The route is auth-guarded; no bearer token is rejected."""
    student = _make_student(db_session)

    r = client_with_uow.get(f"/api/v1/enrollments/student/{student.id}")

    # current behaviour (pinned, not endorsed): the auth error handler maps
    # the missing credentials to 401.
    assert r.status_code == 401


# ── GET /enrollments/group/{group_id}/students-summary ────────────────────────


def test_group_summary_happy_path(
    client_with_uow, override_auth, mock_admin_headers, db_session
):
    """Happy path: a group's current-level enrollment summary is returned."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id, level_number=1)
    _make_group_level(db_session, group.id, course.id, level_number=1, sessions_planned=8)
    student = _make_student(db_session, full_name="Grace Hopper")
    enrollment = _make_enrollment(
        db_session,
        student.id,
        group.id,
        level_number=1,
        amount_due=500.0,
        discount_applied=50.0,
    )

    r = client_with_uow.get(
        f"/api/v1/enrollments/group/{group.id}/students-summary",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] is None
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 1

    data = body["data"][0]
    assert set(data) == _SUMMARY_FIELDS
    assert data["student_id"] == student.id
    assert data["student_name"] == "Grace Hopper"
    assert data["enrollment_id"] == enrollment.id
    assert data["level_number"] == 1
    assert data["status"] == "active"
    assert data["sessions_attended"] == 0
    assert data["sessions_total"] == 8
    assert data["payment_status"] == "not_paid"
    assert data["amount_due"] == 500.0
    assert data["discount_applied"] == 50.0
    # current behaviour (pinned, not endorsed): the summary returns the raw view
    # balance, which is NEGATIVE for an unpaid enrollment (student route returns
    # max(0, -balance) instead).
    assert data["amount_remaining"] == -450.0


def test_group_summary_filters_to_group_current_level_by_default(
    client_with_uow, override_auth, mock_admin_headers, db_session
):
    """Without ?level the summary keeps only the group's current level."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id, level_number=1)
    _make_group_level(db_session, group.id, course.id, level_number=1, sessions_planned=8)
    _make_group_level(db_session, group.id, course.id, level_number=2, sessions_planned=6)
    level1_student = _make_student(db_session)
    level2_student = _make_student(db_session)
    level1 = _make_enrollment(db_session, level1_student.id, group.id, level_number=1)
    level2 = _make_enrollment(db_session, level2_student.id, group.id, level_number=2)

    r = client_with_uow.get(
        f"/api/v1/enrollments/group/{group.id}/students-summary",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    data = r.json()["data"]
    assert {row["enrollment_id"] for row in data} == {level1.id}
    assert {row["level_number"] for row in data} == {1}
    assert level2.id not in {row["enrollment_id"] for row in data}


def test_group_summary_level_query_filter(
    client_with_uow, override_auth, mock_admin_headers, db_session
):
    """?level selects a specific level's enrollments only."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id, level_number=1)
    _make_group_level(db_session, group.id, course.id, level_number=1, sessions_planned=8)
    _make_group_level(db_session, group.id, course.id, level_number=2, sessions_planned=6)
    level1_student = _make_student(db_session)
    level2_student = _make_student(db_session)
    _make_enrollment(db_session, level1_student.id, group.id, level_number=1)
    level2 = _make_enrollment(db_session, level2_student.id, group.id, level_number=2)

    r = client_with_uow.get(
        f"/api/v1/enrollments/group/{group.id}/students-summary?level=2",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    data = r.json()["data"]
    assert {row["enrollment_id"] for row in data} == {level2.id}
    assert {row["level_number"] for row in data} == {2}
    assert data[0]["sessions_total"] == 6


def test_group_summary_level_zero_falls_back_to_group_level(
    client_with_uow, override_auth, mock_admin_headers, db_session
):
    """?level=0 is falsy and silently falls back to the group current level."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id, level_number=1)
    _make_group_level(db_session, group.id, course.id, level_number=1, sessions_planned=8)
    student = _make_student(db_session)
    level1 = _make_enrollment(db_session, student.id, group.id, level_number=1)

    r = client_with_uow.get(
        f"/api/v1/enrollments/group/{group.id}/students-summary?level=0",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    data = r.json()["data"]
    assert {row["enrollment_id"] for row in data} == {level1.id}


def test_group_summary_excludes_dropped_enrollments(
    client_with_uow, override_auth, mock_admin_headers, db_session
):
    """A dropped enrollment is omitted from the group summary."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id, level_number=1)
    _make_group_level(db_session, group.id, course.id, level_number=1, sessions_planned=8)
    active_student = _make_student(db_session)
    dropped_student = _make_student(db_session)
    active = _make_enrollment(db_session, active_student.id, group.id, level_number=1)
    _make_enrollment(
        db_session, dropped_student.id, group.id, level_number=1, status="dropped"
    )

    r = client_with_uow.get(
        f"/api/v1/enrollments/group/{group.id}/students-summary",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    data = r.json()["data"]
    assert {row["enrollment_id"] for row in data} == {active.id}


def test_group_summary_sessions_total_zero_without_level_row(
    client_with_uow, override_auth, mock_admin_headers, db_session
):
    """With no matching group_levels row, sessions_total is 0."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id, level_number=1)
    student = _make_student(db_session)
    enrollment = _make_enrollment(db_session, student.id, group.id, level_number=1)

    r = client_with_uow.get(
        f"/api/v1/enrollments/group/{group.id}/students-summary",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    data = r.json()["data"]
    assert [row["enrollment_id"] for row in data] == [enrollment.id]
    assert data[0]["sessions_total"] == 0


def test_group_summary_unknown_group_returns_empty_list(
    client_with_uow, override_auth, mock_admin_headers
):
    """Unknown group id is a 200 with an empty list, not a 404."""
    r = client_with_uow.get(
        "/api/v1/enrollments/group/999999999/students-summary",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["data"] == []


def test_group_summary_requires_auth(client_with_uow, db_session):
    """The route is auth-guarded; no bearer token is rejected."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)

    r = client_with_uow.get(f"/api/v1/enrollments/group/{group.id}/students-summary")

    assert r.status_code == 401
