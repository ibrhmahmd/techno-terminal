"""Characterization tests for the Academics Group Directory HTTP API (ticket #18, Part 3 of 3).

Pins the exact status codes, response envelopes and field shapes of the 3 read-only
endpoints under ``/api/v1/academics/groups`` served by ``group_directory_router.py``
BEFORE the Academics HTTP layer moves into ``app/modules/academics/api/``:

    GET /academics/groups/grouped
    GET /academics/groups/filter
    GET /academics/groups/{group_id}/enriched

Buckets
-------
* All three endpoints are GETs served by ``GroupDirectoryService``, which opens its
  own ``get_session()``. Rows created via the rollback-only ``uow`` fixture are
  invisible to it, so the tests seed data through the committed ``db_session``
  fixture with uuid-tagged values.
* No Supabase/Twilio/Gmail dependencies — academics endpoints should not need them.

Run
---
GMAIL_SENDER_ADDRESS= GMAIL_APP_PASSWORD= TWILIO_ACCOUNT_SID= TWILIO_AUTH_TOKEN= SUPABASE_URL=http://127.0.0.1:9 /home/ibrahim/Desktop/techno-projects/techno-terminal/.venv/bin/python -m pytest app/modules/academics/tests/characterization/test_academics_group_directory_api.py -q -p no:cacheprovider
"""

import uuid
from datetime import time

from starlette.testclient import TestClient

from app.modules.academics.models.course_models import Course
from app.modules.academics.models.group_models import Group
from app.modules.hr.models.employee_models import Employee


def _short() -> str:
    return uuid.uuid4().hex[:10]


def _make_course(db_session, **overrides) -> Course:
    """Insert a committed course (visible to the services' own sessions)."""
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
    """Insert a committed group (visible to the services' own sessions)."""
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


def _make_employee(db_session, **overrides) -> Employee:
    """Insert a committed employee (visible to the services' own sessions)."""
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


_ENRICHED_FIELDS = {
    "id",
    "group_name",
    "course_id",
    "course_name",
    "instructor_id",
    "instructor_name",
    "level_number",
    "default_day",
    "default_time_start",
    "default_time_end",
    "max_capacity",
    "notes",
    "status",
    "current_student_count",
}


# ── /api/v1/academics/groups/grouped ──────────────────────────────────────────


def test_list_groups_grouped_by_course(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /academics/groups/grouped?group_by=course groups active groups by course."""
    marker = _short()
    emp = _make_employee(db_session, full_name=f"Grouped Inst {marker}")
    course = _make_course(db_session, name=f"Grouped Course {marker}")
    group = _make_group(db_session, course.id, emp.id, name=f"Grouped Group {marker}")

    r = client_with_uow.get(
        f"/api/v1/academics/groups/grouped?group_by=course&search={marker}",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    assert set(data) == {"groups", "total", "group_by"}
    assert data["group_by"] == "course"
    assert data["total"] == 1
    assert len(data["groups"]) == 1
    item = data["groups"][0]
    assert set(item) == {"key", "label", "count", "groups"}
    assert item["key"] == str(course.id)
    assert item["label"] == course.name
    assert item["count"] == 1
    assert set(item["groups"][0]) == _ENRICHED_FIELDS
    assert item["groups"][0]["id"] == group.id
    assert item["groups"][0]["group_name"] == group.name
    assert item["groups"][0]["course_name"] == course.name
    assert item["groups"][0]["instructor_name"] == emp.full_name
    assert item["groups"][0]["status"] == "active"


def test_list_groups_grouped_missing_group_by(client_with_uow, override_auth, mock_admin_headers):
    """GET /academics/groups/grouped without required group_by returns 422."""
    r = client_with_uow.get("/api/v1/academics/groups/grouped", headers=mock_admin_headers)

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


def test_list_groups_grouped_invalid_group_by(client_with_uow, override_auth, mock_admin_headers):
    """GET /academics/groups/grouped?group_by=bogus returns 500 (ValueError unhandled)."""
    test_client = TestClient(client_with_uow.app, raise_server_exceptions=False)
    r = test_client.get(
        "/api/v1/academics/groups/grouped?group_by=bogus",
        headers=mock_admin_headers,
    )

    assert r.status_code == 500
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "InternalServerError"
    # current behaviour (pinned, not endorsed) - service raises bare ValueError


# ── /api/v1/academics/groups/filter ───────────────────────────────────────────


def test_filter_groups_by_course(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /academics/groups/filter?course_ids=<id> returns the matching enriched group."""
    marker = _short()
    course = _make_course(db_session, name=f"Filter Course {marker}")
    group = _make_group(db_session, course.id, name=f"Filter Group {marker}")

    r = client_with_uow.get(
        f"/api/v1/academics/groups/filter?course_ids={course.id}",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    assert set(data) == {"groups", "total", "skip", "limit"}
    assert data["skip"] == 0
    assert data["limit"] == 50
    assert data["total"] >= 1
    assert isinstance(data["groups"], list)
    match = [g for g in data["groups"] if g["id"] == group.id]
    assert len(match) == 1
    assert set(match[0]) == _ENRICHED_FIELDS
    assert match[0]["group_name"] == group.name
    assert match[0]["course_name"] == course.name


def test_filter_groups_bad_date(client_with_uow, override_auth, mock_admin_headers):
    """GET /academics/groups/filter with a malformed date returns 422."""
    r = client_with_uow.get(
        "/api/v1/academics/groups/filter?start_date_from=not-a-date",
        headers=mock_admin_headers,
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"
    assert "invalid date/time format" in body["message"].lower()


# ── /api/v1/academics/groups/{group_id}/enriched ──────────────────────────────


def test_get_enriched_group_by_id(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /academics/groups/{group_id}/enriched returns the enriched group."""
    marker = _short()
    emp = _make_employee(db_session, full_name=f"Enriched Inst {marker}")
    course = _make_course(db_session, name=f"Enriched Course {marker}")
    group = _make_group(
        db_session,
        course.id,
        emp.id,
        name=f"Enriched Group {marker}",
        level_number=2,
        default_day="Monday",
        max_capacity=12,
        notes=f"notes {marker}",
    )

    r = client_with_uow.get(
        f"/api/v1/academics/groups/{group.id}/enriched",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    assert set(data) == _ENRICHED_FIELDS
    assert data["id"] == group.id
    assert data["group_name"] == group.name
    assert data["course_id"] == course.id
    assert data["course_name"] == course.name
    assert data["instructor_id"] == emp.id
    assert data["instructor_name"] == emp.full_name
    assert data["level_number"] == 2
    assert data["default_day"] == "Monday"
    assert data["default_time_start"] == "14:00:00"
    assert data["default_time_end"] == "16:00:00"
    assert data["max_capacity"] == 12
    assert data["notes"] == f"notes {marker}"
    assert data["status"] == "active"
    assert data["current_student_count"] == 0


def test_get_enriched_group_not_found(client_with_uow, override_auth, mock_admin_headers):
    """GET /academics/groups/999999999/enriched returns 404 from the directory router."""
    r = client_with_uow.get(
        "/api/v1/academics/groups/999999999/enriched",
        headers=mock_admin_headers,
    )

    assert r.status_code == 404
    body = r.json()
    assert set(body) == {"success", "error", "message"}
    assert body["success"] is False
    assert body["error"] == "NotFound"
    assert body["message"] == "Group 999999999 not found"


def test_enriched_route_not_shadowed_by_group_id(client_with_uow, override_auth, mock_admin_headers, db_session):
    """Route-order pin: /{group_id}/enriched resolves to the directory router.

    If groups_router (GET /academics/groups/{group_id}) shadowed this route the
    response would not carry the enriched ``group_name`` payload.
    """
    marker = _short()
    course = _make_course(db_session, name=f"Shadow Course {marker}")
    group = _make_group(db_session, course.id, name=f"Shadow Group {marker}")

    r = client_with_uow.get(
        f"/api/v1/academics/groups/{group.id}/enriched",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    assert r.json()["data"]["group_name"] == group.name
    assert "course_name" in r.json()["data"]


def test_grouped_and_filter_not_shadowed_by_group_id(client_with_uow, override_auth, mock_admin_headers):
    """Route-order pin: literal /grouped and /filter are not parsed as group_id."""
    r_grouped = client_with_uow.get(
        "/api/v1/academics/groups/grouped?group_by=status",
        headers=mock_admin_headers,
    )
    assert r_grouped.status_code == 200

    r_filter = client_with_uow.get(
        "/api/v1/academics/groups/filter",
        headers=mock_admin_headers,
    )
    assert r_filter.status_code == 200


def test_group_directory_endpoints_require_auth(client):
    """All three endpoints without auth return 401."""
    r_grouped = client.get("/api/v1/academics/groups/grouped?group_by=day")
    assert r_grouped.status_code == 401

    r_filter = client.get("/api/v1/academics/groups/filter")
    assert r_filter.status_code == 401

    r_enriched = client.get("/api/v1/academics/groups/1/enriched")
    assert r_enriched.status_code == 401
