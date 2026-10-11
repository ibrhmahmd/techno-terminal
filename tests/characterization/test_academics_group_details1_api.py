"""Characterization tests for the Academics Group Details HTTP API (ticket #18, Part 2 of 3).

Pins the exact status codes, response envelopes and field shapes of 3 endpoints
served by ``app/modules/academics/api/group_details_router.py`` BEFORE the Academics
HTTP layer moves into ``app/modules/academics/api/``:

    DELETE /academics/groups/{group_id}/levels/{level_number}
    GET    /academics/groups/{group_id}/levels/detailed
    GET    /academics/groups/{group_id}/attendance

Buckets
-------
* All three services open their own ``get_session()``; rows created via the
  rollback-only ``uow`` fixture are invisible to them. Tests therefore seed data
  through the committed ``db_session`` fixture with uuid-tagged values.
* ``delete_level`` really COMMITS (and hard-deletes the level row); each test
  creates its own course/group/levels so reruns do not collide and shared rows
  are untouched.
* No Supabase/Twilio/Gmail dependencies — academics endpoints do not need them.

Run
---
GMAIL_SENDER_ADDRESS= GMAIL_APP_PASSWORD= TWILIO_ACCOUNT_SID= TWILIO_AUTH_TOKEN= SUPABASE_URL=http://127.0.0.1:9 /home/ibrahim/Desktop/techno-projects/techno-terminal/.venv/bin/python -m pytest tests/characterization/test_academics_group_details1_api.py -q -p no:cacheprovider
"""

import uuid
from datetime import date, time

from app.modules.academics.models.course_models import Course
from app.modules.academics.models.group_level_models import GroupLevel
from app.modules.academics.models.group_models import Group
from app.modules.academics.models.session_models import CourseSession


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


# ── DELETE /api/v1/academics/groups/{group_id}/levels/{level_number} ───────────


def test_delete_level_happy_path(client_with_uow, override_auth, mock_admin_headers, db_session):
    """DELETE the latest level (2) of a 2-level group returns the cascade counts."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id, level_number=2)
    _make_group_level(db_session, group.id, course.id, level_number=1, status="active")
    level2 = _make_group_level(db_session, group.id, course.id, level_number=2, status="active")
    _make_session(db_session, group.id, level_number=2, session_number=1, group_level_id=level2.id)

    r = client_with_uow.delete(
        f"/api/v1/academics/groups/{group.id}/levels/2",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Level 2 deleted successfully."
    data = body["data"]
    assert set(data) == {
        "level_number_deleted",
        "reverted_to_level",
        "sessions_deleted",
        "enrollments_deleted",
        "enrollments_reactivated",
        "payments_voided",
        "group_level_number_after",
    }
    assert data["level_number_deleted"] == 2
    assert data["reverted_to_level"] == 1
    assert data["sessions_deleted"] == 1
    assert data["enrollments_deleted"] == 0
    assert data["enrollments_reactivated"] == 0
    assert data["payments_voided"] == 0
    assert data["group_level_number_after"] == 1


def test_delete_level_unknown_group_is_404(client_with_uow, override_auth, mock_admin_headers):
    """DELETE a level on a nonexistent group returns 404."""
    r = client_with_uow.delete(
        "/api/v1/academics/groups/999999999/levels/2",
        headers=mock_admin_headers,
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFound"
    assert body["message"] == "Group 999999999 not found"


def test_delete_level_unknown_level_is_404(client_with_uow, override_auth, mock_admin_headers, db_session):
    """DELETE a level number that does not exist for an existing group returns 404."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    _make_group_level(db_session, group.id, course.id, level_number=1)

    r = client_with_uow.delete(
        f"/api/v1/academics/groups/{group.id}/levels/9",
        headers=mock_admin_headers,
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFound"
    assert body["message"] == f"Level 9 not found for group {group.id}"


def test_delete_level_only_level_is_409(client_with_uow, override_auth, mock_admin_headers, db_session):
    """DELETE level 1 of a single-level group returns 409 (cannot delete first/only)."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id, level_number=1)
    _make_group_level(db_session, group.id, course.id, level_number=1)

    r = client_with_uow.delete(
        f"/api/v1/academics/groups/{group.id}/levels/1",
        headers=mock_admin_headers,
    )

    assert r.status_code == 409
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "Conflict"
    assert body["message"] == "Cannot delete the first/only level of a group"


def test_delete_level_not_latest_is_409(client_with_uow, override_auth, mock_admin_headers, db_session):
    """DELETE a non-latest level of a multi-level group returns 409.

    Pinned quirk: deleting level 1 of a group whose latest level is 2 is rejected as
    "not the latest level" (the "first level" rule is never reached).
    """
    course = _make_course(db_session)
    group = _make_group(db_session, course.id, level_number=2)
    _make_group_level(db_session, group.id, course.id, level_number=1)
    _make_group_level(db_session, group.id, course.id, level_number=2)

    r = client_with_uow.delete(
        f"/api/v1/academics/groups/{group.id}/levels/1",
        headers=mock_admin_headers,
    )

    assert r.status_code == 409
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "Conflict"
    assert body["message"] == f"Can only delete the latest level 2 for group {group.id}"


def test_delete_level_invalid_number_is_422(client_with_uow, override_auth, mock_admin_headers, db_session):
    """DELETE with level_number < 1 fails path validation with 422."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)

    r = client_with_uow.delete(
        f"/api/v1/academics/groups/{group.id}/levels/0",
        headers=mock_admin_headers,
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


def test_delete_level_requires_admin(client):
    """DELETE a level without auth returns 401."""
    r = client.delete("/api/v1/academics/groups/1/levels/2")

    assert r.status_code == 401
    body = r.json()
    assert body["success"] is False


# ── GET /api/v1/academics/groups/{group_id}/levels/detailed ────────────────────

_LEVEL_FIELDS = {
    "level_number",
    "level_id",
    "course_id",
    "instructor_id",
    "status",
    "start_date",
    "end_date",
    "sessions",
    "students_count",
    "students_completed",
    "students_dropped",
    "payment_summary",
}

_SESSION_FIELDS = {
    "session_id",
    "session_number",
    "date",
    "time_start",
    "time_end",
    "status",
    "is_extra_session",
    "actual_instructor_id",
    "is_substitute",
}


def test_get_levels_detailed_all(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET without level_number returns all levels with lookup tables and sessions."""
    course = _make_course(db_session, name=f"Detailed Course {_short()}")
    group = _make_group(db_session, course.id, level_number=2)
    _make_group_level(db_session, group.id, course.id, level_number=1, status="completed")
    level2 = _make_group_level(db_session, group.id, course.id, level_number=2, status="active")
    _make_session(db_session, group.id, level_number=2, session_number=1, group_level_id=level2.id)

    r = client_with_uow.get(
        f"/api/v1/academics/groups/{group.id}/levels/detailed",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Levels loaded successfully."
    data = body["data"]
    assert set(data) == {"group_id", "generated_at", "cache_ttl", "courses", "instructors", "levels"}
    assert data["group_id"] == group.id
    assert data["cache_ttl"] == 300
    assert data["courses"][str(course.id)] == {"course_id": course.id, "course_name": course.name}
    assert data["instructors"] == {}
    assert len(data["levels"]) == 2
    levels_by_number = {lv["level_number"]: lv for lv in data["levels"]}
    assert set(levels_by_number) == {1, 2}
    lv2 = levels_by_number[2]
    assert set(lv2) == _LEVEL_FIELDS
    assert lv2["level_id"] == level2.id
    assert lv2["course_id"] == course.id
    assert lv2["instructor_id"] == 0
    assert lv2["status"] == "active"
    assert lv2["start_date"] == "2026-06-15"
    assert lv2["end_date"] == "2026-06-15"
    assert len(lv2["sessions"]) == 1
    assert set(lv2["sessions"][0]) == _SESSION_FIELDS
    assert lv2["sessions"][0]["session_number"] == 1
    assert set(lv2["payment_summary"]) == {
        "total_expected",
        "total_collected",
        "total_due",
        "collection_rate",
        "unpaid_students_count",
    }


def test_get_levels_detailed_single(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET with level_number returns only that level and a level-specific message."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id, level_number=2)
    level1 = _make_group_level(db_session, group.id, course.id, level_number=1, status="completed")
    _make_group_level(db_session, group.id, course.id, level_number=2, status="active")

    r = client_with_uow.get(
        f"/api/v1/academics/groups/{group.id}/levels/detailed?level_number=1",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["message"] == "Level 1 loaded successfully."
    assert len(body["data"]["levels"]) == 1
    assert body["data"]["levels"][0]["level_id"] == level1.id


def test_get_levels_detailed_unknown_group_is_200_empty(client_with_uow, override_auth, mock_admin_headers):
    """GET for a nonexistent group returns 200 with empty lookups — no 404.

    Pinned quirk (not endorsed): an unknown group is indistinguishable from an
    existing group that has no levels.
    """
    r = client_with_uow.get(
        "/api/v1/academics/groups/999999999/levels/detailed",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["group_id"] == 999999999
    assert data["courses"] == {}
    assert data["instructors"] == {}
    assert data["levels"] == []


def test_get_levels_detailed_unknown_level_is_200_empty(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET for an existing group with a nonexistent level_number returns 200 empty."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    _make_group_level(db_session, group.id, course.id, level_number=1)

    r = client_with_uow.get(
        f"/api/v1/academics/groups/{group.id}/levels/detailed?level_number=9",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["message"] == "Level 9 loaded successfully."
    assert body["data"]["levels"] == []


def test_get_levels_detailed_invalid_level_number_is_422(client_with_uow, override_auth, mock_admin_headers):
    """GET with level_number < 1 fails query validation with 422."""
    r = client_with_uow.get(
        "/api/v1/academics/groups/1/levels/detailed?level_number=0",
        headers=mock_admin_headers,
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


# ── GET /api/v1/academics/groups/{group_id}/attendance ─────────────────────────


def test_get_attendance_grid_happy_path(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET attendance returns roster + sessions with per-session attendance map."""
    course = _make_course(db_session)
    group = _make_group(db_session, course.id)
    level = _make_group_level(db_session, group.id, course.id, level_number=1)
    _make_session(
        db_session, group.id, level_number=1, session_number=1,
        group_level_id=level.id, notes="first",
    )

    r = client_with_uow.get(
        f"/api/v1/academics/groups/{group.id}/attendance?level_number=1",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Attendance grid loaded successfully."
    data = body["data"]
    assert set(data) == {"group_id", "level_number", "generated_at", "cache_ttl", "roster", "sessions"}
    assert data["group_id"] == group.id
    assert data["level_number"] == 1
    assert data["cache_ttl"] == 300
    assert data["roster"] == []
    assert len(data["sessions"]) == 1
    session = data["sessions"][0]
    assert set(session) == {
        "session_id",
        "session_number",
        "date",
        "time_start",
        "time_end",
        "status",
        "is_extra_session",
        "notes",
        "attendance",
    }
    assert session["session_number"] == 1
    assert session["date"] == "2026-06-15"
    assert session["status"] == "scheduled"
    assert session["notes"] == "first"
    assert session["attendance"] == {}


def test_get_attendance_unknown_group_is_200_empty(client_with_uow, override_auth, mock_admin_headers):
    """GET attendance for a nonexistent group returns 200 empty — no 404."""
    r = client_with_uow.get(
        "/api/v1/academics/groups/999999999/attendance?level_number=1",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["group_id"] == 999999999
    assert data["level_number"] == 1
    assert data["roster"] == []
    assert data["sessions"] == []


def test_get_attendance_missing_level_number_is_422(client_with_uow, override_auth, mock_admin_headers):
    """GET attendance without the required level_number returns 422."""
    r = client_with_uow.get(
        "/api/v1/academics/groups/1/attendance",
        headers=mock_admin_headers,
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


def test_get_attendance_invalid_level_number_is_422(client_with_uow, override_auth, mock_admin_headers):
    """GET attendance with level_number < 1 fails query validation with 422."""
    r = client_with_uow.get(
        "/api/v1/academics/groups/1/attendance?level_number=0",
        headers=mock_admin_headers,
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"
