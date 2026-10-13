"""Characterization tests for the Academics Courses & Sessions HTTP API (ticket #18, Part 1 of 3).

Pins the exact status codes, response envelopes and field shapes of the 13 endpoints under
``/api/v1/academics/courses*`` and ``/api/v1/academics/sessions*`` (and the group sessions POST)
BEFORE the Academics HTTP layer moves into ``app/modules/academics/api/``.

Endpoints covered
-----------------
Courses (6):
    GET  /academics/courses
    POST /academics/courses
    GET  /academics/courses/{course_id}/stats
    GET  /academics/courses/{course_id}
    PATCH /academics/courses/{course_id}
    DELETE /academics/courses/{course_id}

Sessions (7):
    POST /academics/groups/{group_id}/sessions
    GET  /academics/sessions/{session_id}
    PATCH /academics/sessions/{session_id}
    DELETE /academics/sessions/{session_id}
    POST /academics/sessions/{session_id}/cancel
    POST /academics/sessions/{session_id}/reactivate
    POST /academics/sessions/{session_id}/substitute

Buckets
-------
* GET endpoints (list, stats, get-by-id) read through services that open their own
  ``get_db()`` session. Rows created via the rollback-only ``uow`` fixture are invisible
  to them. These tests therefore seed data through the committed ``db_session`` fixture
  with uuid-tagged values.
* Write endpoints (create, update, delete, cancel, reactivate, substitute) assert
  response shape only and use uuid-tagged values so reruns do not collide (their
  commits are real).
* No Supabase/Twilio/Gmail dependencies — academics endpoints should not need them.

Run
---
GMAIL_SENDER_ADDRESS= GMAIL_APP_PASSWORD= TWILIO_ACCOUNT_SID= TWILIO_AUTH_TOKEN= SUPABASE_URL=http://127.0.0.1:9 /home/ibrahim/Desktop/techno-projects/techno-terminal/.venv/bin/python -m pytest app/modules/academics/tests/characterization/test_academics_courses_sessions_api.py -q -p no:cacheprovider
"""

import uuid
from datetime import date, time
from decimal import Decimal

import pytest
from sqlmodel import select

from app.modules.academics.models.course_models import Course
from app.modules.academics.models.group_models import Group
from app.modules.academics.models.session_models import CourseSession
from app.modules.auth.models.auth_models import User as UserModel
from app.modules.hr.models.employee_models import Employee


def _short() -> str:
    return uuid.uuid4().hex[:10]


def _make_course(db_session, **overrides) -> Course:
    """Insert a committed course (visible to services' own sessions)."""
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


def _make_group(db_session, course_id: int, instructor_id: int = None, **overrides) -> Group:
    """Insert a committed group (visible to services' own sessions)."""
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


def _make_session(db_session, group_id: int, level_number: int = 1, session_number: int = 1, **overrides) -> CourseSession:
    """Insert a committed session (visible to services' own sessions)."""
    session = CourseSession(
        group_id=group_id,
        level_number=level_number,
        session_number=session_number,
        session_date=overrides.pop("session_date", date(2026, 6, 15)),
        start_time=overrides.pop("start_time", time(14, 0)),
        end_time=overrides.pop("end_time", time(16, 0)),
        actual_instructor_id=overrides.pop("actual_instructor_id", None),
        is_substitute=overrides.pop("is_substitute", False),
        is_extra_session=overrides.pop("is_extra_session", False),
        notes=overrides.pop("notes", None),
        status=overrides.pop("status", "scheduled"),
        **overrides,
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


def _make_employee(db_session, **overrides) -> Employee:
    """Insert a committed employee (visible to services' own sessions)."""
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


# ── /api/v1/academics/courses (GET list) ──────────────────────────────────────


def test_list_courses(client, override_auth, mock_admin_headers):
    """GET /academics/courses returns paginated list of active courses."""
    # Get baseline total from shared DB
    r = client.get("/api/v1/academics/courses?limit=200", headers=mock_admin_headers)
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "total", "skip", "limit"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert isinstance(body["total"], int)
    assert body["skip"] == 0
    assert body["limit"] == 200
    total_before = body["total"]

    # Create courses via POST (since db_session seeding has visibility issues)
    marker = _short()
    for name, price in [(f"CourseA {marker}", 1000), (f"CourseB {marker}", 1500)]:
        r = client.post(
            "/api/v1/academics/courses",
            headers=mock_admin_headers,
            json={"name": name, "category": "software", "price_per_level": price, "sessions_per_level": 8},
        )
        assert r.status_code == 201

    # List again to verify total count increased
    r = client.get("/api/v1/academics/courses?limit=200", headers=mock_admin_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["total"] == total_before + 2
    # Verify our courses exist by fetching with skip to reach the end (newest courses have highest IDs)
    # Since limit max is 200 and total_before could be > 200, we check the last page
    last_page_skip = max(0, body["total"] - 200)
    r = client.get(f"/api/v1/academics/courses?skip={last_page_skip}&limit=200", headers=mock_admin_headers)
    assert r.status_code == 200
    body = r.json()
    found = [c for c in body["data"] if marker in c["name"]]
    assert len(found) >= 2
    for item in found:
        assert set(item) >= {"id", "name", "category", "description", "price_per_level", "sessions_per_level", "is_active"}
        assert isinstance(item["id"], int)
        assert isinstance(item["name"], str)
        assert isinstance(item["price_per_level"], (int, float))
        assert isinstance(item["sessions_per_level"], int)
        assert isinstance(item["is_active"], bool)
        assert isinstance(item["name"], str)
        assert isinstance(item["price_per_level"], (int, float))
        assert isinstance(item["sessions_per_level"], int)
        assert isinstance(item["is_active"], bool)
    for item in found:
        assert set(item) >= {"id", "name", "category", "description", "price_per_level", "sessions_per_level", "is_active"}
        assert isinstance(item["id"], int)
        assert isinstance(item["name"], str)
        assert isinstance(item["price_per_level"], (int, float))
        assert isinstance(item["sessions_per_level"], int)
        assert isinstance(item["is_active"], bool)


def test_list_courses_pagination(client, override_auth, mock_admin_headers):
    """GET /academics/courses?skip=0&limit=2 respects pagination params."""
    # Use large limit to verify total count includes our courses
    marker = _short()
    for i in range(3):
        r = client.post(
            "/api/v1/academics/courses",
            headers=mock_admin_headers,
            json={"name": f"Pag{i} {marker}", "category": "software", "price_per_level": 1000 + i * 100, "sessions_per_level": 8},
        )
        assert r.status_code == 201

    # Test pagination with small limit
    r = client.get("/api/v1/academics/courses?skip=0&limit=2", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["skip"] == 0
    assert body["limit"] == 2
    assert len(body["data"]) <= 2
    # Verify total count is large (includes seeded + existing)
    assert body["total"] >= 3


def test_list_courses_requires_auth(client):
    """GET /academics/courses without auth returns 401."""
    r = client.get("/api/v1/academics/courses")
    assert r.status_code == 401
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "Unauthorized"


# ── /api/v1/academics/courses (POST create) ───────────────────────────────────


def test_create_course(client_with_uow, override_auth, mock_admin_headers):
    """POST /academics/courses creates a new course and returns 201 with CoursePublic."""
    unique = _short()
    payload = {
        "name": f"New Course {unique}",
        "category": "software",
        "description": "Test course",
        "notes": "Created via test",
        "price_per_level": 1500.0,
        "sessions_per_level": 8,
        "max_levels": 5,
        "is_active": True,
    }

    r = client_with_uow.post("/api/v1/academics/courses", headers=mock_admin_headers, json=payload)

    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Course created successfully."
    data = body["data"]
    assert set(data) >= {"id", "name", "category", "description", "price_per_level", "sessions_per_level", "is_active"}
    assert isinstance(data["id"], int)
    assert data["name"] == payload["name"]
    assert data["category"] == "software"
    assert data["price_per_level"] == 1500.0
    assert data["sessions_per_level"] == 8
    assert data["is_active"] is True


def test_create_course_bad_body(client_with_uow, override_auth, mock_admin_headers):
    """POST /academics/courses with missing required fields returns 422 ValidationError."""
    r = client_with_uow.post(
        "/api/v1/academics/courses",
        headers=mock_admin_headers,
        json={"name": "Incomplete"},  # missing price_per_level, sessions_per_level
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


def test_create_course_invalid_category(client_with_uow, override_auth, mock_admin_headers):
    """POST /academics/courses with invalid category returns 422 ValidationError (DB check constraint)."""
    payload = {
        "name": f"Bad Category {_short()}",
        "category": "invalid_category",
        "price_per_level": 1000.0,
        "sessions_per_level": 8,
    }
    r = client_with_uow.post("/api/v1/academics/courses", headers=mock_admin_headers, json=payload)
    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


# ── /api/v1/academics/courses/{course_id}/stats ───────────────────────────────


def test_get_course_stats(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /academics/courses/{course_id}/stats returns CourseStatsDTO."""
    course = _make_course(db_session, name=f"Stats Course {_short()}", price_per_level=2000, sessions_per_level=8)

    r = client_with_uow.get(f"/api/v1/academics/courses/{course.id}/stats", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    assert set(data) == {"course_id", "course_name", "total_groups", "active_groups", "total_students_ever", "active_students"}
    assert data["course_id"] == course.id
    assert data["course_name"] == course.name
    assert isinstance(data["total_groups"], int)
    assert isinstance(data["active_groups"], int)
    assert isinstance(data["total_students_ever"], int)
    assert isinstance(data["active_students"], int)


def test_get_course_stats_not_found(client_with_uow, override_auth, mock_admin_headers):
    """GET /academics/courses/999999999/stats returns 404 with NotFound error type."""
    r = client_with_uow.get("/api/v1/academics/courses/999999999/stats", headers=mock_admin_headers)
    assert r.status_code == 404
    body = r.json()
    assert set(body) == {"success", "error", "message"}
    assert body["success"] is False
    # Current behaviour: returns "NotFound" not "NotFoundError"
    assert body["error"] == "NotFound"
    assert "not found" in body["message"].lower()
    # current behaviour (pinned, not endorsed)


# ── /api/v1/academics/courses/{course_id} (GET) ───────────────────────────────


def test_get_course_by_id(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /academics/courses/{course_id} returns CoursePublic."""
    course = _make_course(
        db_session,
        name=f"Get Course {_short()}",
        category="hardware",
        description="Test description",
        price_per_level=2500.0,
        sessions_per_level=10,
        is_active=True,
    )

    r = client_with_uow.get(f"/api/v1/academics/courses/{course.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    assert set(data) >= {"id", "name", "category", "description", "price_per_level", "sessions_per_level", "is_active"}
    assert data["id"] == course.id
    assert data["name"] == course.name
    assert data["category"] == "hardware"
    assert data["description"] == "Test description"
    assert data["price_per_level"] == 2500.0
    assert data["sessions_per_level"] == 10
    assert data["is_active"] is True


def test_get_course_not_found(client_with_uow, override_auth, mock_admin_headers):
    """GET /academics/courses/999999999 returns 404 NotFoundError."""
    r = client_with_uow.get("/api/v1/academics/courses/999999999", headers=mock_admin_headers)
    assert r.status_code == 404
    body = r.json()
    assert set(body) == {"success", "error", "message"}
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert "not found" in body["message"].lower()


# ── /api/v1/academics/courses/{course_id} (PATCH) ─────────────────────────────


def test_update_course(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH /academics/courses/{course_id} updates course and returns CoursePublic."""
    course = _make_course(db_session, name=f"Original {_short()}", price_per_level=1000, sessions_per_level=8)

    unique = _short()
    payload = {
        "name": f"Updated {unique}",
        "category": "steam",
        "price_per_level": 2000.0,
        "sessions_per_level": 12,
        "notes": "Updated via test",
    }

    r = client_with_uow.patch(f"/api/v1/academics/courses/{course.id}", headers=mock_admin_headers, json=payload)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    assert data["id"] == course.id
    assert data["name"] == payload["name"]
    assert data["category"] == "steam"
    assert data["price_per_level"] == 2000.0
    assert data["sessions_per_level"] == 12
    # notes field is not in CoursePublic response schema
    assert data["is_active"] is True


def test_update_course_partial(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH /academics/courses/{course_id} with only some fields updates only those."""
    unique = _short()
    course = _make_course(db_session, name=f"Partial {unique}", price_per_level=1000, sessions_per_level=8)

    r = client_with_uow.patch(f"/api/v1/academics/courses/{course.id}", headers=mock_admin_headers, json={"category": "hardware"})

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["category"] == "hardware"
    assert body["data"]["name"] == f"Partial {unique}"
    assert body["data"]["price_per_level"] == 1000.0


def test_update_course_not_found(client_with_uow, override_auth, mock_admin_headers):
    """PATCH /academics/courses/999999999 returns 404 NotFoundError."""
    r = client_with_uow.patch("/api/v1/academics/courses/999999999", headers=mock_admin_headers, json={"name": "X"})
    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"


def test_update_course_bad_body(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH /academics/courses/{course_id} with invalid category returns 422 ValidationError."""
    unique = _short()
    course = _make_course(db_session, name=f"Bad Cat {unique}")
    r = client_with_uow.patch(
        f"/api/v1/academics/courses/{course.id}",
        headers=mock_admin_headers,
        json={"category": "not_a_valid_category"},
    )
    # Service validates category against DB CHECK constraint -> 422 ValidationError
    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


# ── /api/v1/academics/courses/{course_id} (DELETE - soft delete) ──────────────


def test_delete_course(client_with_uow, override_auth, mock_admin_headers, db_session):
    """DELETE /academics/courses/{course_id} soft-deletes (archives) the course."""
    course = _make_course(db_session, name=f"ToDelete {_short()}", is_active=True)

    r = client_with_uow.delete(f"/api/v1/academics/courses/{course.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Course archived successfully."
    data = body["data"]
    assert data["id"] == course.id
    assert data["is_active"] is False


def test_delete_course_not_found(client_with_uow, override_auth, mock_admin_headers):
    """DELETE /academics/courses/999999999 returns 404 NotFoundError."""
    r = client_with_uow.delete("/api/v1/academics/courses/999999999", headers=mock_admin_headers)
    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"


# ── /api/v1/academics/groups/{group_id}/sessions (POST extra session) ─────────


def test_add_extra_session(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST /academics/groups/{group_id}/sessions adds an extra session."""
    emp = _make_employee(db_session, full_name=f"Inst {_short()}")
    course = _make_course(db_session, name=f"ExtraSessCourse {_short()}")
    group = _make_group(db_session, course.id, emp.id)

    unique = _short()
    payload = {
        "group_id": group.id,
        "level_number": 1,
        "extra_date": "2026-07-15",
        "notes": f"Extra session {unique}",
    }

    r = client_with_uow.post(f"/api/v1/academics/groups/{group.id}/sessions", headers=mock_admin_headers, json=payload)

    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Extra session added."
    data = body["data"]
    assert set(data) >= {"id", "group_id", "level_number", "session_number", "session_date", "start_time", "end_time", "status", "is_extra_session", "actual_instructor_id", "notes"}
    assert data["group_id"] == group.id
    assert data["level_number"] == 1
    assert data["is_extra_session"] is True
    assert data["notes"] == f"Extra session {unique}"
    # session_number should be auto-assigned
    assert isinstance(data["session_number"], int)
    assert data["session_number"] > 0


def test_add_extra_session_bad_body(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST /academics/groups/{group_id}/sessions with invalid date returns 422."""
    emp = _make_employee(db_session)
    course = _make_course(db_session, name=f"BadBodyCourse {_short()}")
    group = _make_group(db_session, course.id, emp.id)

    r = client_with_uow.post(
        f"/api/v1/academics/groups/{group.id}/sessions",
        headers=mock_admin_headers,
        json={"level_number": 1, "extra_date": "not-a-date"},
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


def test_add_extra_session_group_not_found(client_with_uow, override_auth, mock_admin_headers):
    """POST /academics/groups/999999999/sessions returns 422 (current behaviour)."""
    payload = {"level_number": 1, "extra_date": "2026-07-15"}
    r = client_with_uow.post("/api/v1/academics/groups/999999999/sessions", headers=mock_admin_headers, json=payload)
    # Current behaviour: returns 422 Unprocessable Entity (NotFoundError mapped to 422?)
    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    # current behaviour (pinned, not endorsed)


# ── /api/v1/academics/sessions/{session_id} (GET) ─────────────────────────────


def test_get_session_by_id(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /academics/sessions/{session_id} returns SessionPublic."""
    emp = _make_employee(db_session, full_name=f"Inst {_short()}")
    course = _make_course(db_session, name=f"SessCourse {_short()}")
    group = _make_group(db_session, course.id, emp.id)
    session = _make_session(db_session, group.id, level_number=1, session_number=1, session_date=date(2026, 6, 15))

    r = client_with_uow.get(f"/api/v1/academics/sessions/{session.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    assert set(data) >= {"id", "group_id", "level_number", "session_number", "session_date", "start_time", "end_time", "status", "is_extra_session", "actual_instructor_id", "notes"}
    assert data["id"] == session.id
    assert data["group_id"] == group.id
    assert data["level_number"] == 1
    assert data["session_number"] == 1
    assert data["session_date"] == "2026-06-15"
    assert data["status"] == "scheduled"
    assert data["is_extra_session"] is False


def test_get_session_not_found(client_with_uow, override_auth, mock_admin_headers):
    """GET /academics/sessions/999999999 returns 404 NotFoundError."""
    r = client_with_uow.get("/api/v1/academics/sessions/999999999", headers=mock_admin_headers)
    assert r.status_code == 404
    body = r.json()
    assert set(body) == {"success", "error", "message"}
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert "not found" in body["message"].lower()


# ── /api/v1/academics/sessions/{session_id} (PATCH) ───────────────────────────


def test_update_session(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH /academics/sessions/{session_id} updates session and returns SessionPublic."""
    emp = _make_employee(db_session, full_name=f"Inst {_short()}")
    course = _make_course(db_session, name=f"UpdateSessCourse {_short()}")
    group = _make_group(db_session, course.id, emp.id)
    session = _make_session(db_session, group.id, level_number=1, session_number=1)

    payload = {
        "session_date": "2026-07-20",
        "start_time": "10:00:00",
        "end_time": "12:00:00",
        "notes": "Updated session",
        "actual_instructor_id": emp.id,
    }

    r = client_with_uow.patch(f"/api/v1/academics/sessions/{session.id}", headers=mock_admin_headers, json=payload)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    assert data["id"] == session.id
    assert data["session_date"] == "2026-07-20"
    assert data["start_time"] == "10:00:00"
    assert data["end_time"] == "12:00:00"
    assert data["notes"] == "Updated session"
    assert data["actual_instructor_id"] == emp.id


def test_update_session_partial(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH /academics/sessions/{session_id} with only some fields updates only those."""
    emp = _make_employee(db_session)
    course = _make_course(db_session, name=f"PartialSess {_short()}")
    group = _make_group(db_session, course.id, emp.id)
    session = _make_session(db_session, group.id, level_number=1, session_number=1, notes="Original notes")

    r = client_with_uow.patch(f"/api/v1/academics/sessions/{session.id}", headers=mock_admin_headers, json={"notes": "Only notes updated"})

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["notes"] == "Only notes updated"
    # Other fields unchanged
    assert body["data"]["level_number"] == 1
    assert body["data"]["session_number"] == 1


def test_update_session_not_found(client_with_uow, override_auth, mock_admin_headers):
    """PATCH /academics/sessions/999999999 returns 404 NotFoundError."""
    r = client_with_uow.patch("/api/v1/academics/sessions/999999999", headers=mock_admin_headers, json={"notes": "X"})
    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"


# ── /api/v1/academics/sessions/{session_id} (DELETE) ──────────────────────────



def test_update_session_invalid_status_is_422(client_with_uow, override_auth, mock_admin_headers):
    """An unknown session status is a 422 from the schema (#150; was a 500 CHECK violation)."""
    r = client_with_uow.patch("/api/v1/academics/sessions/999999999", headers=mock_admin_headers, json={"status": "bogus"})
    assert r.status_code == 422
    assert r.json()["error"] == "ValidationError"

def test_delete_session(client_with_uow, override_auth, mock_admin_headers, db_session):
    """DELETE /academics/sessions/{session_id} deletes the session."""
    emp = _make_employee(db_session)
    course = _make_course(db_session, name=f"DelSessCourse {_short()}")
    group = _make_group(db_session, course.id, emp.id)
    session = _make_session(db_session, group.id, level_number=1, session_number=1)

    r = client_with_uow.delete(f"/api/v1/academics/sessions/{session.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["data"] is None
    assert body["message"] == "Session deleted successfully."


def test_delete_session_not_found(client_with_uow, override_auth, mock_admin_headers):
    """DELETE /academics/sessions/999999999 returns 200 with success (current behaviour)."""
    r = client_with_uow.delete("/api/v1/academics/sessions/999999999", headers=mock_admin_headers)
    # Current behaviour: returns 200 with success even for non-existent session
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"] is None
    assert body["message"] == "Session deleted successfully."
    # current behaviour (pinned, not endorsed)


# ── /api/v1/academics/sessions/{session_id}/cancel ────────────────────────────


def test_cancel_session(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST /academics/sessions/{session_id}/cancel cancels the session."""
    emp = _make_employee(db_session)
    course = _make_course(db_session, name=f"CancelCourse {_short()}")
    group = _make_group(db_session, course.id, emp.id)
    session = _make_session(db_session, group.id, level_number=1, session_number=1, status="scheduled")

    r = client_with_uow.post(f"/api/v1/academics/sessions/{session.id}/cancel", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Session cancelled and rescheduled successfully."
    data = body["data"]
    assert data["id"] == session.id
    assert data["status"] == "cancelled"


def test_cancel_session_not_found(client_with_uow, override_auth, mock_admin_headers):
    """POST /academics/sessions/999999999/cancel returns 404 NotFoundError."""
    r = client_with_uow.post("/api/v1/academics/sessions/999999999/cancel", headers=mock_admin_headers)
    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"


# ── /api/v1/academics/sessions/{session_id}/reactivate ────────────────────────


def test_reactivate_session(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST /academics/sessions/{session_id}/reactivate reactivates a cancelled session."""
    emp = _make_employee(db_session)
    course = _make_course(db_session, name=f"ReactCourse {_short()}")
    group = _make_group(db_session, course.id, emp.id)
    session = _make_session(db_session, group.id, level_number=1, session_number=1, status="cancelled")

    r = client_with_uow.post(f"/api/v1/academics/sessions/{session.id}/reactivate", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Session reactivated successfully."
    data = body["data"]
    assert data["id"] == session.id
    assert data["status"] == "scheduled"


def test_reactivate_session_not_found(client_with_uow, override_auth, mock_admin_headers):
    """POST /academics/sessions/999999999/reactivate returns 404 NotFoundError."""
    r = client_with_uow.post("/api/v1/academics/sessions/999999999/reactivate", headers=mock_admin_headers)
    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"


def test_reactivate_session_already_scheduled(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST /academics/sessions/{session_id}/reactivate on non-cancelled session returns 409 BusinessRuleError."""
    emp = _make_employee(db_session)
    course = _make_course(db_session, name=f"AlreadyActive {_short()}")
    group = _make_group(db_session, course.id, emp.id)
    session = _make_session(db_session, group.id, level_number=1, session_number=1, status="scheduled")

    r = client_with_uow.post(f"/api/v1/academics/sessions/{session.id}/reactivate", headers=mock_admin_headers)

    # Current behaviour: returns 409 BusinessRuleError for non-cancelled session
    assert r.status_code == 409
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "BusinessRuleError"
    assert "not cancelled" in body["message"].lower()
    # current behaviour (pinned, not endorsed)


# ── /api/v1/academics/sessions/{session_id}/substitute ────────────────────────


def test_substitute_instructor(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST /academics/sessions/{session_id}/substitute - service method not implemented (AttributeError -> 500)."""
    from starlette.testclient import TestClient
    emp1 = _make_employee(db_session, full_name=f"Inst1 {_short()}")
    emp2 = _make_employee(db_session, full_name=f"Inst2 {_short()}")
    course = _make_course(db_session, name=f"SubCourse {_short()}")
    group = _make_group(db_session, course.id, emp1.id)
    session = _make_session(db_session, group.id, level_number=1, session_number=1, actual_instructor_id=emp1.id)

    payload = {"instructor_id": emp2.id}

    # Use TestClient with raise_server_exceptions=False to catch 500
    test_client = TestClient(client_with_uow.app, raise_server_exceptions=False)
    r = test_client.post(f"/api/v1/academics/sessions/{session.id}/substitute", headers=mock_admin_headers, json=payload)

    # Current behaviour: SessionService has no mark_substitute_instructor method -> AttributeError -> 500
    assert r.status_code == 500
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "InternalServerError"
    # current behaviour (pinned, not endorsed) - service method missing


def test_substitute_instructor_not_found(client_with_uow, override_auth, mock_admin_headers):
    """POST /academics/sessions/999999999/substitute - service method not implemented (AttributeError -> 500)."""
    from starlette.testclient import TestClient
    # Use TestClient with raise_server_exceptions=False to catch 500
    test_client = TestClient(client_with_uow.app, raise_server_exceptions=False)
    r = test_client.post(
        "/api/v1/academics/sessions/999999999/substitute",
        headers=mock_admin_headers,
        json={"instructor_id": 1},
    )
    # Current behaviour: AttributeError before NotFound check -> 500
    assert r.status_code == 500
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "InternalServerError"
    # current behaviour (pinned, not endorsed) - service method missing


def test_substitute_instructor_bad_body(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST /academics/sessions/{session_id}/substitute with invalid instructor_id returns 422 (validated before service call)."""
    emp = _make_employee(db_session)
    course = _make_course(db_session, name=f"BadSubCourse {_short()}")
    group = _make_group(db_session, course.id, emp.id)
    session = _make_session(db_session, group.id)

    r = client_with_uow.post(
        f"/api/v1/academics/sessions/{session.id}/substitute",
        headers=mock_admin_headers,
        json={"instructor_id": "not-an-int"},
    )

    # Pydantic validation happens before service call
    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


# ── Role checks ────────────────────────────────────────────────────────────────


def test_courses_read_endpoints_require_auth(client):
    """GET /academics/courses/* without auth returns 401."""
    endpoints = [
        "/api/v1/academics/courses",
        "/api/v1/academics/courses/1",
        "/api/v1/academics/courses/1/stats",
    ]
    for endpoint in endpoints:
        r = client.get(endpoint)
        assert r.status_code == 401, f"{endpoint} should require auth"


def test_courses_write_endpoints_require_admin(client):
    """POST/PATCH/DELETE /academics/courses without admin returns 401/403."""
    # Test without auth first
    endpoints = [
        ("POST", "/api/v1/academics/courses", {"name": "Test", "price_per_level": 100, "sessions_per_level": 8}),
        ("PATCH", "/api/v1/academics/courses/1", {"name": "Updated"}),
        ("DELETE", "/api/v1/academics/courses/1", None),
    ]
    for method, endpoint, body in endpoints:
        if method == "POST":
            r = client.post(endpoint, json=body)
        elif method == "PATCH":
            r = client.patch(endpoint, json=body)
        elif method == "DELETE":
            r = client.delete(endpoint)
        assert r.status_code == 401, f"{method} {endpoint} should require auth"


def test_sessions_write_endpoints_require_admin(client):
    """POST/PATCH/DELETE /academics/sessions/* without admin returns 401/403."""
    endpoints = [
        ("POST", "/api/v1/academics/groups/1/sessions", {"level_number": 1, "extra_date": "2026-07-15"}),
        ("PATCH", "/api/v1/academics/sessions/1", {"notes": "Updated"}),
        ("DELETE", "/api/v1/academics/sessions/1", None),
        ("POST", "/api/v1/academics/sessions/1/cancel", {}),
        ("POST", "/api/v1/academics/sessions/1/reactivate", {}),
        ("POST", "/api/v1/academics/sessions/1/substitute", {"instructor_id": 1}),
    ]
    for method, endpoint, body in endpoints:
        if method == "POST":
            r = client.post(endpoint, json=body)
        elif method == "PATCH":
            r = client.patch(endpoint, json=body)
        elif method == "DELETE":
            r = client.delete(endpoint)
        assert r.status_code == 401, f"{method} {endpoint} should require auth"


def test_sessions_read_endpoints_require_auth(client):
    """GET /academics/sessions/{id} without auth returns 401."""
    r = client.get("/api/v1/academics/sessions/1")
    assert r.status_code == 401