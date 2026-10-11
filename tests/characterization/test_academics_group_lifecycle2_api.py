"""Characterization tests for the Academics Group Lifecycle HTTP API (ticket #18, analytics slice).

Pins the exact status codes, envelopes and field shapes of the 4 analytics/history
endpoints served by ``app/modules/academics/api/group_lifecycle_router.py`` BEFORE
the Academics HTTP layer moves into ``app/modules/academics/api/``:

    GET /academics/groups/{group_id}/enrollments/analytics
    GET /academics/groups/{group_id}/instructors/analytics
    GET /academics/groups/{group_id}/enrollment-history      (alias)
    GET /academics/groups/{group_id}/instructor-history      (alias)

Buckets
-------
* ``GroupAnalyticsService`` opens its own ``get_session()``; rows created via the
  rollback-only ``uow`` fixture are invisible to it. Every test seeds committed
  course/group/employee/student/enrollment rows through the ``db_session`` fixture
  with uuid-tagged values.
* The 4 routes are read-only (GET); nothing is written and no row is deleted.

Pinned quirks
-------------
* There is NO 404 for these routes. ``get_enrollment_history`` and
  ``get_instructor_history`` fall back to ``group_name="Unknown"`` and empty
  aggregates for a nonexistent ``group_id``, so the response is HTTP 200.
* The ``status`` query filter narrows only ``enrollments[]``; the group-level
  ``total_/active_/completed_/dropped_enrollments`` counts are always computed
  over ALL enrollments of the group.
* A level whose status is not ``active`` does not become ``current_instructor``.

Run
---
GMAIL_SENDER_ADDRESS= GMAIL_APP_PASSWORD= TWILIO_ACCOUNT_SID= TWILIO_AUTH_TOKEN= SUPABASE_URL=http://127.0.0.1:9 /home/ibrahim/Desktop/techno-projects/techno-terminal/.venv/bin/python -m pytest tests/characterization/test_academics_group_lifecycle2_api.py -q -p no:cacheprovider
"""

import uuid
from datetime import date, datetime, time, timezone

from app.modules.academics.models.course_models import Course
from app.modules.academics.models.group_level_models import GroupLevel
from app.modules.academics.models.group_models import Group
from app.modules.crm.models.student_models import Student
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.hr.models.employee_models import Employee


def _short() -> str:
    return uuid.uuid4().hex[:10]


def _make_course(db_session, **overrides) -> Course:
    """Insert a committed course (visible to the service's own session)."""
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


def _make_employee(db_session, **overrides) -> Employee:
    """Insert a committed employee (visible to the service's own session)."""
    emp = Employee(
        full_name=overrides.pop("full_name", f"Instructor {_short()}"),
        phone=overrides.pop("phone", f"+201{_short()}"),
        email=overrides.pop("email", f"{_short()}@test.com"),
        national_id=overrides.pop("national_id", f"NID{_short()}"),
        university=overrides.pop("university", "Test University"),
        major=overrides.pop("major", "Computer Science"),
        is_graduate=overrides.pop("is_graduate", False),
        job_title=overrides.pop("job_title", "Instructor"),
        employment_type=overrides.pop("employment_type", "full_time"),
        monthly_salary=overrides.pop("monthly_salary", 5000.0),
        contract_percentage=overrides.pop("contract_percentage", None),
        is_active=overrides.pop("is_active", True),
        **overrides,
    )
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)
    return emp


def _make_group(db_session, course_id: int, instructor_id: int = None, **overrides) -> Group:
    """Insert a committed group (visible to the service's own session)."""
    group = Group(
        name=overrides.pop("name", f"Group {_short()}"),
        course_id=course_id,
        instructor_id=instructor_id,
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


def _make_group_level(db_session, group_id: int, course_id: int, **overrides) -> GroupLevel:
    """Insert a committed group level (visible to the service's own session)."""
    level = GroupLevel(
        group_id=group_id,
        level_number=overrides.pop("level_number", 1),
        course_id=course_id,
        instructor_id=overrides.pop("instructor_id", None),
        sessions_planned=overrides.pop("sessions_planned", 8),
        price_override=overrides.pop("price_override", None),
        status=overrides.pop("status", "active"),
        effective_from=overrides.pop(
            "effective_from", datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        ),
        notes=overrides.pop("notes", None),
        **overrides,
    )
    db_session.add(level)
    db_session.commit()
    db_session.refresh(level)
    return level


def _make_student(db_session, **overrides) -> Student:
    """Insert a committed student (visible to the service's own session)."""
    student = Student(
        full_name=overrides.pop("full_name", f"Student {_short()}"),
        date_of_birth=overrides.pop("date_of_birth", None),
        gender=overrides.pop("gender", None),
        phone=overrides.pop("phone", f"+201{_short()}"),
        status=overrides.pop("status", "active"),
        **overrides,
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student


def _make_enrollment(db_session, student_id: int, group_id: int, **overrides) -> Enrollment:
    """Insert a committed enrollment (visible to the service's own session)."""
    enrollment = Enrollment(
        student_id=student_id,
        group_id=group_id,
        level_number=overrides.pop("level_number", 1),
        amount_due=overrides.pop("amount_due", None),
        discount_applied=overrides.pop("discount_applied", 0.0),
        status=overrides.pop("status", "active"),
        enrolled_at=overrides.pop("enrolled_at", date(2024, 3, 1)),
        **overrides,
    )
    db_session.add(enrollment)
    db_session.commit()
    db_session.refresh(enrollment)
    return enrollment


# ── GET /api/v1/academics/groups/{group_id}/enrollments/analytics ─────────────


def test_enrollment_analytics_happy_path(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET enrollment analytics returns stats plus per-enrollment payment math."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    student = _make_student(db_session)
    enrollment = _make_enrollment(
        db_session,
        student.id,
        group.id,
        level_number=2,
        amount_due=1000.0,
        discount_applied=200.0,
        status="active",
        enrolled_at=date(2024, 3, 1),
    )

    r = client_with_uow.get(
        f"/api/v1/academics/groups/{group.id}/enrollments/analytics",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] is None
    data = body["data"]
    assert set(data) == {
        "group_id",
        "group_name",
        "total_enrollments",
        "active_enrollments",
        "completed_enrollments",
        "dropped_enrollments",
        "enrollments",
    }
    assert data["group_id"] == group.id
    assert data["group_name"] == group.name
    assert data["total_enrollments"] == 1
    assert data["active_enrollments"] == 1
    assert data["completed_enrollments"] == 0
    assert data["dropped_enrollments"] == 0
    assert len(data["enrollments"]) == 1
    item = data["enrollments"][0]
    assert set(item) == {
        "enrollment_id",
        "student_id",
        "student_name",
        "student_phone",
        "level_number_at_enrollment",
        "enrolled_at",
        "status",
        "amount_due",
        "discount_applied",
        "payments_made",
        "balance_remaining",
    }
    assert item["enrollment_id"] == enrollment.id
    assert item["student_id"] == student.id
    assert item["student_name"] == student.full_name
    assert item["student_phone"] == student.phone
    assert item["level_number_at_enrollment"] == 2
    assert item["enrolled_at"] == "2024-03-01"
    assert item["status"] == "active"
    assert item["amount_due"] == 1000.0
    assert item["discount_applied"] == 200.0
    assert item["payments_made"] == 0.0
    assert item["balance_remaining"] == 800.0


def test_enrollment_analytics_unknown_group_is_200_unknown(client_with_uow, override_auth, mock_admin_headers):
    """GET analytics for a nonexistent group is 200 with group_name='Unknown' (no 404)."""
    r = client_with_uow.get(
        "/api/v1/academics/groups/999999999/enrollments/analytics",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["group_id"] == 999999999
    assert data["group_name"] == "Unknown"
    assert data["total_enrollments"] == 0
    assert data["active_enrollments"] == 0
    assert data["completed_enrollments"] == 0
    assert data["dropped_enrollments"] == 0
    assert data["enrollments"] == []


def test_enrollment_analytics_status_filter_keeps_unfiltered_totals(
    client_with_uow, override_auth, mock_admin_headers, db_session
):
    """The status filter narrows enrollments[] but group-level stats stay over ALL rows."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    active_student = _make_student(db_session)
    completed_student = _make_student(db_session)
    _make_enrollment(db_session, active_student.id, group.id, status="active")
    _make_enrollment(db_session, completed_student.id, group.id, status="completed")

    r = client_with_uow.get(
        f"/api/v1/academics/groups/{group.id}/enrollments/analytics",
        headers=mock_admin_headers,
        params={"status": "active"},
    )

    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total_enrollments"] == 2
    assert data["active_enrollments"] == 1
    assert data["completed_enrollments"] == 1
    assert data["dropped_enrollments"] == 0
    assert len(data["enrollments"]) == 1
    assert data["enrollments"][0]["status"] == "active"


def test_enrollment_analytics_limit_zero_is_422(client_with_uow, override_auth, mock_admin_headers):
    """limit is constrained to ge=1, so limit=0 fails request validation."""
    r = client_with_uow.get(
        "/api/v1/academics/groups/1/enrollments/analytics",
        headers=mock_admin_headers,
        params={"limit": 0},
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"
    assert "details" in body


def test_enrollment_analytics_bad_group_id_is_422(client_with_uow, override_auth, mock_admin_headers):
    """A non-integer group_id fails path validation with 422."""
    r = client_with_uow.get(
        "/api/v1/academics/groups/not-an-int/enrollments/analytics",
        headers=mock_admin_headers,
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"
    assert "details" in body


# ── GET /api/v1/academics/groups/{group_id}/instructors/analytics ─────────────


def test_instructor_analytics_happy_path(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET instructor analytics returns the assignment summary with current instructor."""
    course = _make_course(db_session)
    instructor = _make_employee(db_session)
    group = _make_group(db_session, course.id, instructor_id=instructor.id)
    _make_group_level(
        db_session,
        group.id,
        course.id,
        instructor_id=instructor.id,
        status="active",
        effective_from=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
    )

    r = client_with_uow.get(
        f"/api/v1/academics/groups/{group.id}/instructors/analytics",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] is None
    data = body["data"]
    assert set(data) == {
        "group_id",
        "group_name",
        "total_instructors",
        "current_instructor",
        "instructors",
    }
    assert data["group_id"] == group.id
    assert data["group_name"] == group.name
    assert data["total_instructors"] == 1
    assert len(data["instructors"]) == 1
    item = data["instructors"][0]
    assert set(item) == {
        "instructor_id",
        "instructor_name",
        "is_current",
        "levels_taught_count",
        "first_assigned_at",
        "last_assigned_at",
    }
    assert item["instructor_id"] == instructor.id
    assert item["instructor_name"] == instructor.full_name
    assert item["is_current"] is True
    assert item["levels_taught_count"] == 1
    assert isinstance(item["first_assigned_at"], str)
    assert isinstance(item["last_assigned_at"], str)
    assert data["current_instructor"] == item


def test_instructor_analytics_completed_level_not_current(
    client_with_uow, override_auth, mock_admin_headers, db_session
):
    """A non-active level is listed but never becomes current_instructor."""
    course = _make_course(db_session)
    instructor = _make_employee(db_session)
    group = _make_group(db_session, course.id, instructor_id=instructor.id)
    _make_group_level(
        db_session,
        group.id,
        course.id,
        instructor_id=instructor.id,
        status="completed",
    )

    r = client_with_uow.get(
        f"/api/v1/academics/groups/{group.id}/instructors/analytics",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total_instructors"] == 1
    assert data["instructors"][0]["is_current"] is False
    assert data["current_instructor"] is None


def test_instructor_analytics_unknown_group_is_200_empty(client_with_uow, override_auth, mock_admin_headers):
    """GET instructor analytics for a nonexistent group is 200 with empty aggregates."""
    r = client_with_uow.get(
        "/api/v1/academics/groups/999999999/instructors/analytics",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    data = r.json()["data"]
    assert data["group_id"] == 999999999
    assert data["group_name"] == "Unknown"
    assert data["total_instructors"] == 0
    assert data["current_instructor"] is None
    assert data["instructors"] == []


def test_instructor_analytics_bad_group_id_is_422(client_with_uow, override_auth, mock_admin_headers):
    """A non-integer group_id fails path validation with 422."""
    r = client_with_uow.get(
        "/api/v1/academics/groups/not-an-int/instructors/analytics",
        headers=mock_admin_headers,
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"
    assert "details" in body


# ── GET /api/v1/academics/groups/{group_id}/enrollment-history (alias) ────────


def test_enrollment_history_alias_happy_path(client_with_uow, override_auth, mock_admin_headers, db_session):
    """The alias returns the same payload shape as /enrollments/analytics."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    student = _make_student(db_session)
    _make_enrollment(
        db_session,
        student.id,
        group.id,
        level_number=3,
        amount_due=500.0,
        discount_applied=50.0,
        status="active",
        enrolled_at=date(2024, 4, 2),
    )

    r = client_with_uow.get(
        f"/api/v1/academics/groups/{group.id}/enrollment-history",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    assert set(data) == {
        "group_id",
        "group_name",
        "total_enrollments",
        "active_enrollments",
        "completed_enrollments",
        "dropped_enrollments",
        "enrollments",
    }
    assert data["total_enrollments"] == 1
    assert data["enrollments"][0]["level_number_at_enrollment"] == 3
    assert data["enrollments"][0]["enrolled_at"] == "2024-04-02"
    assert data["enrollments"][0]["balance_remaining"] == 450.0


def test_enrollment_history_alias_limit_over_max_is_422(client_with_uow, override_auth, mock_admin_headers):
    """limit is capped at le=500, so limit=501 fails request validation."""
    r = client_with_uow.get(
        "/api/v1/academics/groups/1/enrollment-history",
        headers=mock_admin_headers,
        params={"limit": 501},
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"
    assert "details" in body


# ── GET /api/v1/academics/groups/{group_id}/instructor-history (alias) ────────


def test_instructor_history_alias_happy_path(client_with_uow, override_auth, mock_admin_headers, db_session):
    """The alias returns the same payload shape as /instructors/analytics."""
    course = _make_course(db_session)
    instructor = _make_employee(db_session)
    group = _make_group(db_session, course.id, instructor_id=instructor.id)
    _make_group_level(
        db_session,
        group.id,
        course.id,
        instructor_id=instructor.id,
        status="active",
    )

    r = client_with_uow.get(
        f"/api/v1/academics/groups/{group.id}/instructor-history",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    assert set(data) == {
        "group_id",
        "group_name",
        "total_instructors",
        "current_instructor",
        "instructors",
    }
    assert data["group_id"] == group.id
    assert data["group_name"] == group.name
    assert data["total_instructors"] == 1
    assert data["instructors"][0]["instructor_id"] == instructor.id
    assert data["current_instructor"]["instructor_id"] == instructor.id


def test_instructor_history_alias_unknown_group_is_200_empty(client_with_uow, override_auth, mock_admin_headers):
    """The alias also returns 200 with empty aggregates for a nonexistent group."""
    r = client_with_uow.get(
        "/api/v1/academics/groups/999999999/instructor-history",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    data = r.json()["data"]
    assert data["group_name"] == "Unknown"
    assert data["total_instructors"] == 0
    assert data["current_instructor"] is None
    assert data["instructors"] == []
