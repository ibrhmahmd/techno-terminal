"""Characterization tests for the Academics Group Lifecycle HTTP API (ticket #18, Part 3 of 3).

Pins the exact status codes, envelopes and field shapes of the 3 level-lifecycle
endpoints served by ``app/api/routers/academics/group_lifecycle_router.py`` BEFORE
the Academics HTTP layer moves into ``app/modules/academics/api/``:

    GET   /academics/groups/{group_id}/levels/{level_number}
    POST  /academics/groups/{group_id}/levels/{level_number}/cancel
    PATCH /academics/groups/{group_id}/levels/{level_number}

Buckets
-------
* ``GroupLevelService`` opens its own ``get_session()``; rows created via the
  rollback-only ``uow`` fixture are invisible to it. All tests therefore seed
  committed course/group/level rows through the ``db_session`` fixture with
  uuid-tagged names.
* ``cancel_level`` and ``update_level`` really COMMIT; each test creates its own
  course/group/levels so reruns do not collide and shared rows are untouched.
* No Supabase/Twilio/Gmail dependencies — academics endpoints do not need them.

Pinned quirks
-------------
* GET surfaces the service's ``NotFoundError`` through the domain handler, so the
  error key is ``"NotFoundError"``. The cancel/update routes instead convert to
  ``HTTPException`` and the error key is ``"NotFound"``.
* ``ValueError`` (cancel already completed/cancelled) and ``BusinessRuleError``
  (edit a non-active level) are re-mapped to HTTP 400, not 404/409.

Run
---
GMAIL_SENDER_ADDRESS= GMAIL_APP_PASSWORD= TWILIO_ACCOUNT_SID= TWILIO_AUTH_TOKEN= SUPABASE_URL=http://127.0.0.1:9 /home/ibrahim/Desktop/techno-projects/techno-terminal/.venv/bin/python -m pytest tests/characterization/test_academics_group_lifecycle1_api.py -q -p no:cacheprovider
"""

import uuid
from datetime import time
from decimal import Decimal

from app.modules.academics.models.course_models import Course
from app.modules.academics.models.group_level_models import GroupLevel
from app.modules.academics.models.group_models import Group
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
        notes=overrides.pop("notes", None),
        **overrides,
    )
    db_session.add(level)
    db_session.commit()
    db_session.refresh(level)
    return level


# ── GET /api/v1/academics/groups/{group_id}/levels/{level_number} ─────────────


def test_get_level_happy_path(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET an existing level returns the enriched GroupLevelPublic payload."""
    course = _make_course(db_session)
    instructor = _make_employee(db_session)
    group = _make_group(db_session, course.id, instructor_id=instructor.id)
    level = _make_group_level(
        db_session,
        group.id,
        course.id,
        level_number=1,
        instructor_id=instructor.id,
        sessions_planned=12,
        price_override=Decimal("1500.00"),
        notes="pinned-note",
    )

    r = client_with_uow.get(
        f"/api/v1/academics/groups/{group.id}/levels/1",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] is None
    data = body["data"]
    assert set(data) == {
        "id",
        "group_id",
        "level_number",
        "course_id",
        "course_name",
        "instructor_id",
        "instructor_name",
        "sessions_planned",
        "price_override",
        "status",
        "effective_from",
        "effective_to",
        "notes",
        "created_at",
    }
    assert data["id"] == level.id
    assert data["group_id"] == group.id
    assert data["level_number"] == 1
    assert data["course_id"] == course.id
    assert data["course_name"] == course.name
    assert data["instructor_id"] == instructor.id
    assert data["instructor_name"] == instructor.full_name
    assert data["sessions_planned"] == 12
    assert data["price_override"] == 1500.0
    assert data["status"] == "active"
    assert data["effective_to"] is None
    assert data["notes"] == "pinned-note"
    assert isinstance(data["created_at"], str)


def test_get_level_unknown_level_is_404(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET a level number that does not exist returns the domain NotFoundError envelope."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    _make_group_level(db_session, group.id, course.id, level_number=1)

    r = client_with_uow.get(
        f"/api/v1/academics/groups/{group.id}/levels/9",
        headers=mock_admin_headers,
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert body["message"] == f"Level 9 not found for group {group.id}"


def test_get_level_unknown_group_is_404(client_with_uow, override_auth, mock_admin_headers):
    """GET a level on a nonexistent group returns 404 (level lookup fails first)."""
    r = client_with_uow.get(
        "/api/v1/academics/groups/999999999/levels/1",
        headers=mock_admin_headers,
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert body["message"] == "Level 1 not found for group 999999999"


# ── POST /api/v1/academics/groups/{group_id}/levels/{level_number}/cancel ─────


def test_cancel_level_happy_path(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST cancel an active level returns the CancelLevelResult payload."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    level = _make_group_level(db_session, group.id, course.id, level_number=1)

    r = client_with_uow.post(
        f"/api/v1/academics/groups/{group.id}/levels/1/cancel",
        headers=mock_admin_headers,
        json={"reason": "teacher left"},
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Level 1 cancelled successfully."
    data = body["data"]
    assert set(data) == {"level_id", "level_number", "status", "cancelled_at", "reason"}
    assert data["level_id"] == level.id
    assert data["level_number"] == 1
    assert data["status"] == "cancelled"
    assert isinstance(data["cancelled_at"], str)
    assert data["reason"] == "teacher left"


def test_cancel_level_without_reason(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST cancel with an empty body is accepted and echoes reason=null."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    _make_group_level(db_session, group.id, course.id, level_number=1)

    r = client_with_uow.post(
        f"/api/v1/academics/groups/{group.id}/levels/1/cancel",
        headers=mock_admin_headers,
        json={},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["status"] == "cancelled"
    assert body["data"]["reason"] is None


def test_cancel_level_unknown_level_is_404(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST cancel a nonexistent level returns the HTTPException NotFound envelope."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    _make_group_level(db_session, group.id, course.id, level_number=1)

    r = client_with_uow.post(
        f"/api/v1/academics/groups/{group.id}/levels/9/cancel",
        headers=mock_admin_headers,
        json={"reason": "nope"},
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFound"
    assert body["message"] == f"Level 9 not found for group {group.id}"


def test_cancel_level_already_cancelled_is_400(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST cancel a level already in 'cancelled' status returns 400 BadRequest."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    _make_group_level(db_session, group.id, course.id, level_number=1, status="cancelled")

    r = client_with_uow.post(
        f"/api/v1/academics/groups/{group.id}/levels/1/cancel",
        headers=mock_admin_headers,
        json={"reason": "again"},
    )

    assert r.status_code == 400
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "BadRequest"
    assert body["message"] == "Level is already cancelled"


def test_cancel_level_completed_is_400(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST cancel a 'completed' level returns 400 BadRequest."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    _make_group_level(db_session, group.id, course.id, level_number=1, status="completed")

    r = client_with_uow.post(
        f"/api/v1/academics/groups/{group.id}/levels/1/cancel",
        headers=mock_admin_headers,
        json={"reason": "too late"},
    )

    assert r.status_code == 400
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "BadRequest"
    assert body["message"] == "Cannot cancel an already completed level"


def test_cancel_level_reason_too_long_is_422(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST cancel with a reason longer than 500 chars fails request validation."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    _make_group_level(db_session, group.id, course.id, level_number=1)

    r = client_with_uow.post(
        f"/api/v1/academics/groups/{group.id}/levels/1/cancel",
        headers=mock_admin_headers,
        json={"reason": "x" * 501},
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"
    assert "details" in body


# ── PATCH /api/v1/academics/groups/{group_id}/levels/{level_number} ───────────


def test_update_level_happy_path(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH an active level updates fields and returns the enriched payload."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    _make_group_level(db_session, group.id, course.id, level_number=1, sessions_planned=8)

    r = client_with_uow.patch(
        f"/api/v1/academics/groups/{group.id}/levels/1",
        headers=mock_admin_headers,
        json={"price_override": 1750.5, "notes": "updated"},
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Level 1 updated successfully."
    data = body["data"]
    assert data["level_number"] == 1
    assert data["price_override"] == 1750.5
    assert data["notes"] == "updated"
    assert data["status"] == "active"


def test_update_level_unknown_level_is_404(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH a nonexistent level number returns the HTTPException NotFound envelope."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    _make_group_level(db_session, group.id, course.id, level_number=1)

    r = client_with_uow.patch(
        f"/api/v1/academics/groups/{group.id}/levels/9",
        headers=mock_admin_headers,
        json={"notes": "nope"},
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFound"
    assert body["message"] == f"Level 9 not found for group {group.id}"


def test_update_level_non_active_is_400(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH a non-active level returns 400 BadRequest (BusinessRuleError re-mapped)."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    _make_group_level(db_session, group.id, course.id, level_number=1, status="completed")

    r = client_with_uow.patch(
        f"/api/v1/academics/groups/{group.id}/levels/1",
        headers=mock_admin_headers,
        json={"notes": "edit"},
    )

    assert r.status_code == 400
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "BadRequest"
    assert body["message"] == "Cannot edit level 1 with status 'completed'"


def test_update_level_unknown_course_is_404(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH with a course_id that does not exist returns 404 NotFound."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    _make_group_level(db_session, group.id, course.id, level_number=1)

    r = client_with_uow.patch(
        f"/api/v1/academics/groups/{group.id}/levels/1",
        headers=mock_admin_headers,
        json={"course_id": 999999999},
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFound"
    assert body["message"] == "Course 999999999 not found"


def test_update_level_bad_body_is_422(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH with a non-coercible field type fails request validation."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    _make_group_level(db_session, group.id, course.id, level_number=1)

    r = client_with_uow.patch(
        f"/api/v1/academics/groups/{group.id}/levels/1",
        headers=mock_admin_headers,
        json={"instructor_id": "not-an-int"},
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"
    assert "details" in body
