"""Characterization tests for the Academics Groups CRUD HTTP API (ticket #18, Part 1 of 3).

Pins the exact status codes, response envelopes and field shapes of the 5 core
group endpoints under ``/api/v1/academics/groups`` served by ``groups_router.py``
BEFORE the Academics HTTP layer moves into ``app/modules/academics/api/``:

    GET    /academics/groups/{group_id}
    POST   /academics/groups
    PATCH  /academics/groups/{group_id}
    PATCH  /academics/groups/{group_id}/archive
    DELETE /academics/groups/{group_id}

Buckets
-------
* GET reads through ``GroupCoreService``, which opens its own ``get_session()``.
  Rows created via the rollback-only ``uow`` fixture are invisible to it, so the
  test seeds data through the committed ``db_session`` fixture with uuid-tagged
  values.
* Writes (POST/PATCH/archive/DELETE) go through services that open their own
  sessions and really COMMIT; every test uses uuid-tagged names so reruns do not
  collide. Groups are created inside each test and never touch shared rows.
* No Supabase/Twilio/Gmail dependencies — academics endpoints should not need them.

Run
---
GMAIL_SENDER_ADDRESS= GMAIL_APP_PASSWORD= TWILIO_ACCOUNT_SID= TWILIO_AUTH_TOKEN= SUPABASE_URL=http://127.0.0.1:9 /home/ibrahim/Desktop/techno-projects/techno-terminal/.venv/bin/python -m pytest app/modules/academics/tests/characterization/test_academics_groups_crud_api.py -q -p no:cacheprovider
"""

import uuid
from datetime import time

from starlette.testclient import TestClient

from app.modules.academics.models.course_models import Course
from app.modules.academics.models.group_models import Group
from app.modules.hr.models.employee_models import Employee

_GROUP_FIELDS = {
    "id",
    "name",
    "course_id",
    "instructor_id",
    "level_number",
    "max_capacity",
    "default_day",
    "default_time_start",
    "default_time_end",
    "status",
}


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


def _schedule_body(course_id: int, instructor_id: int, **overrides) -> dict:
    return {
        "course_id": course_id,
        "instructor_id": instructor_id,
        "schedule": {
            "day": overrides.pop("day", "Saturday"),
            "time_start": overrides.pop("time_start", "14:00:00"),
            "time_end": overrides.pop("time_end", "16:00:00"),
        },
        "notes": overrides.pop("notes", None),
        "max_capacity": overrides.pop("max_capacity", 15),
        **overrides,
    }


# ── GET /academics/groups/{group_id} ──────────────────────────────────────────


def test_get_group_by_id(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /academics/groups/{id} returns the full group profile."""
    marker = _short()
    emp = _make_employee(db_session, full_name=f"Get Inst {marker}")
    course = _make_course(db_session, name=f"Get Course {marker}")
    group = _make_group(
        db_session,
        course.id,
        emp.id,
        name=f"Get Group {marker}",
        level_number=2,
        max_capacity=12,
        default_day="Monday",
        status="active",
    )

    r = client_with_uow.get(f"/api/v1/academics/groups/{group.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    assert set(data) == _GROUP_FIELDS
    assert data["id"] == group.id
    assert data["name"] == group.name
    assert data["course_id"] == course.id
    assert data["instructor_id"] == emp.id
    assert data["level_number"] == 2
    assert data["max_capacity"] == 12
    assert data["default_day"] == "Monday"
    assert data["default_time_start"] == "14:00:00"
    assert data["default_time_end"] == "16:00:00"
    assert data["status"] == "active"


def test_get_group_not_found(client_with_uow, override_auth, mock_admin_headers):
    """GET /academics/groups/999999999 returns 404 with the NotFoundError envelope."""
    r = client_with_uow.get("/api/v1/academics/groups/999999999", headers=mock_admin_headers)

    assert r.status_code == 404
    body = r.json()
    assert set(body) == {"success", "error", "message"}
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert body["message"] == "Group 999999999 not found."


# ── POST /academics/groups ────────────────────────────────────────────────────


def test_create_group(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST /academics/groups creates Level 1 + sessions and returns 201."""
    emp = _make_employee(db_session)
    course = _make_course(db_session, name=f"Create Course {_short()}", sessions_per_level=4)

    r = client_with_uow.post(
        "/api/v1/academics/groups",
        headers=mock_admin_headers,
        json=_schedule_body(course.id, emp.id, max_capacity=9),
    )

    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Group created with Level 1 and 4 sessions."
    data = body["data"]
    assert set(data) == _GROUP_FIELDS
    assert isinstance(data["id"], int)
    assert data["course_id"] == course.id
    assert data["instructor_id"] == emp.id
    assert data["level_number"] == 1
    assert data["max_capacity"] == 9
    assert data["default_day"] == "Saturday"
    assert data["default_time_start"] == "14:00:00"
    assert data["default_time_end"] == "16:00:00"
    assert data["status"] == "active"
    assert isinstance(data["name"], str) and data["name"]


def test_create_group_missing_schedule(client_with_uow, override_auth, mock_admin_headers):
    """POST /academics/groups without the required schedule returns 422."""
    r = client_with_uow.post(
        "/api/v1/academics/groups",
        headers=mock_admin_headers,
        json={"course_id": 1, "instructor_id": 1},
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


def test_create_group_unknown_course(client_with_uow, override_auth, mock_admin_headers):
    """POST /academics/groups with an unknown course returns 500 (bare ValueError).

    Current behaviour (pinned, not endorsed): the lifecycle service raises
    ``ValueError`` which the router does not map to a 404.
    """
    test_client = TestClient(client_with_uow.app, raise_server_exceptions=False)
    r = test_client.post(
        "/api/v1/academics/groups",
        headers=mock_admin_headers,
        json=_schedule_body(999999999, 1),
    )

    assert r.status_code == 500
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "InternalServerError"


# ── PATCH /academics/groups/{group_id} ────────────────────────────────────────


def test_update_group(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH /academics/groups/{id} updates the provided fields."""
    marker = _short()
    course = _make_course(db_session, name=f"Upd Course {marker}")
    group = _make_group(db_session, course.id, name=f"Upd Group {marker}", max_capacity=15)

    new_name = f"Upd Renamed {marker}"
    r = client_with_uow.patch(
        f"/api/v1/academics/groups/{group.id}",
        headers=mock_admin_headers,
        json={"name": new_name, "max_capacity": 7},
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    assert set(data) == _GROUP_FIELDS
    assert data["id"] == group.id
    assert data["name"] == new_name
    assert data["max_capacity"] == 7
    assert data["status"] == "active"


def test_update_group_not_found(client_with_uow, override_auth, mock_admin_headers):
    """PATCH /academics/groups/999999999 returns 404."""
    r = client_with_uow.patch(
        "/api/v1/academics/groups/999999999",
        headers=mock_admin_headers,
        json={"name": "Nope"},
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert body["message"] == "Group 999999999 not found."


# ── PATCH /academics/groups/{group_id}/archive ────────────────────────────────


def test_archive_group(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH /academics/groups/{id}/archive sets status 'completed'."""
    marker = _short()
    course = _make_course(db_session, name=f"Arch Course {marker}")
    group = _make_group(db_session, course.id, name=f"Arch Group {marker}", status="active")

    r = client_with_uow.patch(
        f"/api/v1/academics/groups/{group.id}/archive",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Group archived successfully."
    data = body["data"]
    assert set(data) == _GROUP_FIELDS
    assert data["id"] == group.id
    assert data["status"] == "completed"


def test_archive_group_not_found(client_with_uow, override_auth, mock_admin_headers):
    """PATCH /academics/groups/999999999/archive returns 404."""
    r = client_with_uow.patch(
        "/api/v1/academics/groups/999999999/archive",
        headers=mock_admin_headers,
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert body["message"] == "Group 999999999 not found."


# ── DELETE /academics/groups/{group_id} ───────────────────────────────────────


def test_delete_group(client_with_uow, override_auth, mock_admin_headers, db_session):
    """DELETE /academics/groups/{id} sets status 'inactive' (not a hard delete)."""
    marker = _short()
    course = _make_course(db_session, name=f"Del Course {marker}")
    group = _make_group(db_session, course.id, name=f"Del Group {marker}", status="active")

    r = client_with_uow.delete(
        f"/api/v1/academics/groups/{group.id}",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Group deactivated successfully."
    data = body["data"]
    assert set(data) == _GROUP_FIELDS
    assert data["id"] == group.id
    assert data["status"] == "inactive"


def test_delete_group_not_found(client_with_uow, override_auth, mock_admin_headers):
    """DELETE /academics/groups/999999999 returns 404."""
    r = client_with_uow.delete(
        "/api/v1/academics/groups/999999999",
        headers=mock_admin_headers,
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert body["message"] == "Group 999999999 not found."


# ── Auth ──────────────────────────────────────────────────────────────────────


def test_groups_crud_endpoints_require_auth(client):
    """All five endpoints without auth return 401."""
    assert client.get("/api/v1/academics/groups/1").status_code == 401
    assert client.post(
        "/api/v1/academics/groups",
        json=_schedule_body(1, 1),
    ).status_code == 401
    assert client.patch(
        "/api/v1/academics/groups/1",
        json={"name": "Nope"},
    ).status_code == 401
    assert client.patch("/api/v1/academics/groups/1/archive").status_code == 401
    assert client.delete("/api/v1/academics/groups/1").status_code == 401
