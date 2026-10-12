"""Characterization tests for the Academics Group sessions/level HTTP API (ticket #18, Part 1 of 3).

Pins the exact status codes, response envelopes and field shapes of 3 endpoints
served by ``app/modules/academics/api/groups_router.py`` BEFORE the Academics HTTP
layer moves into ``app/modules/academics/api/``:

    POST /academics/groups/{group_id}/progress-level
    GET  /academics/groups/{group_id}/sessions
    POST /academics/groups/{group_id}/generate-sessions

Buckets
-------
* GET reads go through ``SessionService``, which opens its own ``get_session()``.
  Rows created via the rollback-only ``uow`` fixture are invisible to it, so the
  test seeds data through the committed ``db_session`` fixture with uuid-tagged
  values.
* Writes (progress-level, generate-sessions) run in services that open their own
  sessions and really COMMIT; every test uses uuid-tagged data and creates its own
  course/group so reruns do not collide and shared rows are untouched.
* No Supabase/Twilio/Gmail dependencies — academics endpoints do not need them.

Run
---
GMAIL_SENDER_ADDRESS= GMAIL_APP_PASSWORD= TWILIO_ACCOUNT_SID= TWILIO_AUTH_TOKEN= SUPABASE_URL=http://127.0.0.1:9 /home/ibrahim/Desktop/techno-projects/techno-terminal/.venv/bin/python -m pytest app/modules/academics/tests/characterization/test_academics_groups_sessions_api.py -q -p no:cacheprovider
"""

import uuid
from datetime import date, time

from app.modules.academics.models.course_models import Course
from app.modules.academics.models.group_level_models import GroupLevel
from app.modules.academics.models.group_models import Group
from app.modules.academics.models.session_models import CourseSession

_SESSION_FIELDS = {
    "id",
    "group_id",
    "level_number",
    "session_number",
    "session_date",
    "start_time",
    "end_time",
    "status",
    "is_extra_session",
    "actual_instructor_id",
    "notes",
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
        sessions_per_level=overrides.pop("sessions_per_level", 3),
        is_active=overrides.pop("is_active", True),
        **overrides,
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    return course


def _make_group(db_session, course_id: int, **overrides) -> Group:
    """Insert a committed group (visible to the services' own sessions)."""
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


def _make_group_level(
    db_session, group_id: int, course_id: int, level_number: int = 1,
    status: str = "active", sessions_planned: int = 3,
) -> GroupLevel:
    """Insert a committed group level (visible to the services' own sessions)."""
    level = GroupLevel(
        group_id=group_id,
        level_number=level_number,
        course_id=course_id,
        status=status,
        sessions_planned=sessions_planned,
    )
    db_session.add(level)
    db_session.commit()
    db_session.refresh(level)
    return level


def _make_session(
    db_session, group_id: int, level_number: int = 1, session_number: int = 1,
    group_level_id: int = None, **overrides,
) -> CourseSession:
    """Insert a committed session (visible to the services' own sessions)."""
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
        group_level_id=group_level_id,
        **overrides,
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


# ── POST /api/v1/academics/groups/{group_id}/progress-level ────────────────────


def test_progress_group_level(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST /academics/groups/{group_id}/progress-level returns ProgressGroupLevelResult."""
    course = _make_course(db_session, sessions_per_level=3)
    group = _make_group(db_session, course.id, level_number=1)
    _make_group_level(db_session, group.id, course.id, level_number=1, sessions_planned=3)

    r = client_with_uow.post(
        f"/api/v1/academics/groups/{group.id}/progress-level",
        headers=mock_admin_headers,
        json={"auto_migrate_enrollments": False},
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    assert set(data) == {
        "old_level_number",
        "new_level_number",
        "enrollments_migrated",
        "sessions_created",
        "message",
    }
    assert data["old_level_number"] == 1
    assert data["new_level_number"] == 2
    assert data["enrollments_migrated"] == 0
    assert data["sessions_created"] == 3
    assert isinstance(data["message"], str)
    assert body["message"] == data["message"]


def test_progress_group_level_no_active_level(client_with_uow, override_auth, mock_admin_headers):
    """POST /academics/groups/999999999/progress-level with a body returns 400 (router maps ValueError)."""
    r = client_with_uow.post(
        "/api/v1/academics/groups/999999999/progress-level",
        headers=mock_admin_headers,
        json={},
    )
    # Current behaviour: ValueError from the lifecycle service becomes HTTPException(400).
    assert r.status_code == 400
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "BadRequest"
    # current behaviour (pinned, not endorsed) - an unknown group is a 400, not 404


def test_progress_group_level_missing_body(client_with_uow, override_auth, mock_admin_headers):
    """POST /academics/groups/999999999/progress-level with no JSON body returns 422."""
    r = client_with_uow.post(
        "/api/v1/academics/groups/999999999/progress-level",
        headers=mock_admin_headers,
    )
    # Current behaviour: the body is required even though every field has a default.
    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"
    # current behaviour (pinned, not endorsed)


def test_progress_group_level_requires_admin(client):
    """POST /academics/groups/1/progress-level without auth returns 401."""
    r = client.post("/api/v1/academics/groups/1/progress-level", json={})
    assert r.status_code == 401
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "Unauthorized"


# ── GET /api/v1/academics/groups/{group_id}/sessions ───────────────────────────


def test_list_group_sessions_by_level(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /academics/groups/{group_id}/sessions?level=1 lists that level's sessions."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    level = _make_group_level(db_session, group.id, course.id, level_number=1)
    s1 = _make_session(db_session, group.id, level_number=1, session_number=1, group_level_id=level.id)
    s2 = _make_session(db_session, group.id, level_number=1, session_number=2, group_level_id=level.id)
    other = _make_group_level(db_session, group.id, course.id, level_number=2, status="completed")
    _make_session(db_session, group.id, level_number=2, session_number=1, group_level_id=other.id)

    r = client_with_uow.get(
        f"/api/v1/academics/groups/{group.id}/sessions?level=1",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] is None
    ids = {item["id"] for item in body["data"]}
    assert ids == {s1.id, s2.id}
    for item in body["data"]:
        assert set(item) >= _SESSION_FIELDS
        assert item["group_id"] == group.id
        assert item["level_number"] == 1
        assert isinstance(item["id"], int)
        assert isinstance(item["session_number"], int)


def test_list_group_sessions_defaults_to_active_level(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /academics/groups/{group_id}/sessions without level returns the active level's sessions."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    level = _make_group_level(db_session, group.id, course.id, level_number=1, status="active")
    session = _make_session(db_session, group.id, level_number=1, session_number=1, group_level_id=level.id)

    r = client_with_uow.get(
        f"/api/v1/academics/groups/{group.id}/sessions",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert [item["id"] for item in body["data"]] == [session.id]


def test_list_group_sessions_unknown_group_returns_empty(client_with_uow, override_auth, mock_admin_headers):
    """GET /academics/groups/999999999/sessions returns 200 with an empty list (no 404)."""
    r = client_with_uow.get(
        "/api/v1/academics/groups/999999999/sessions",
        headers=mock_admin_headers,
    )
    # Current behaviour: unknown group yields an empty list, not a 404.
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"] == []
    # current behaviour (pinned, not endorsed)


def test_list_group_sessions_requires_auth(client):
    """GET /academics/groups/1/sessions without auth returns 401."""
    r = client.get("/api/v1/academics/groups/1/sessions")
    assert r.status_code == 401
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "Unauthorized"


# ── POST /api/v1/academics/groups/{group_id}/generate-sessions ─────────────────


def test_generate_level_sessions(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST /academics/groups/{group_id}/generate-sessions creates sessions_per_level sessions."""
    course = _make_course(db_session, sessions_per_level=4)
    group = _make_group(db_session, course.id)
    _make_group_level(db_session, group.id, course.id, level_number=1)

    r = client_with_uow.post(
        f"/api/v1/academics/groups/{group.id}/generate-sessions",
        headers=mock_admin_headers,
        json={"level_number": 1, "start_date": "2026-07-04"},
    )

    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Generated 4 sessions for level 1."
    assert len(body["data"]) == 4
    for item in body["data"]:
        assert set(item) >= _SESSION_FIELDS
        assert item["group_id"] == group.id
        assert item["level_number"] == 1
        assert item["status"] == "scheduled"
        assert item["is_extra_session"] is False
    assert [item["session_number"] for item in body["data"]] == [1, 2, 3, 4]


def test_generate_level_sessions_group_not_found(client_with_uow, override_auth, mock_admin_headers):
    """POST /academics/groups/999999999/generate-sessions returns 404 NotFoundError."""
    r = client_with_uow.post(
        "/api/v1/academics/groups/999999999/generate-sessions",
        headers=mock_admin_headers,
        json={"level_number": 1, "start_date": "2026-07-04"},
    )
    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert "not found" in body["message"].lower()


def test_generate_level_sessions_already_exist(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST /academics/groups/{group_id}/generate-sessions for a populated level returns 409."""
    course = _make_course(db_session, sessions_per_level=4)
    group = _make_group(db_session, course.id)
    level = _make_group_level(db_session, group.id, course.id, level_number=1)
    _make_session(db_session, group.id, level_number=1, session_number=1, group_level_id=level.id)

    r = client_with_uow.post(
        f"/api/v1/academics/groups/{group.id}/generate-sessions",
        headers=mock_admin_headers,
        json={"level_number": 1, "start_date": "2026-07-04"},
    )

    assert r.status_code == 409
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "BusinessRuleError"
    assert "already has" in body["message"].lower()


def test_generate_level_sessions_missing_level_number(client_with_uow, override_auth, mock_admin_headers):
    """POST /academics/groups/1/generate-sessions without level_number returns 422."""
    r = client_with_uow.post(
        "/api/v1/academics/groups/1/generate-sessions",
        headers=mock_admin_headers,
        json={"start_date": "2026-07-04"},
    )
    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


def test_generate_level_sessions_requires_admin(client):
    """POST /academics/groups/1/generate-sessions without auth returns 401."""
    r = client.post(
        "/api/v1/academics/groups/1/generate-sessions",
        json={"level_number": 1, "start_date": "2026-07-04"},
    )
    assert r.status_code == 401
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "Unauthorized"
