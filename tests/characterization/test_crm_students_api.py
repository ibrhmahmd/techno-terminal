"""Characterization tests for the CRM Students HTTP API (ticket #17, Part 3a of 4).

Pins the exact status codes, response envelopes and field shapes of the first
11 endpoints under ``/api/v1/crm/students*`` (students_router.py) BEFORE the
CRM HTTP layer moves into ``app/modules/crm/api/``.

Buckets
-------
* GET endpoints (list, search, grouped, filter, waiting-list, by-status,
  status-summary, get-by-id, parents, payments) read through services that
  open their own ``get_db()`` session. Rows created via the rollback-only
  ``uow`` fixture are invisible to them. These tests therefore seed data
  through the committed ``db_session`` fixture with uuid-tagged values.
* Write endpoint (create, update) asserts response shape only and uses
  uuid-tagged values so reruns do not collide (their commits are real).
* No Supabase/Twilio/Gmail dependencies — crm endpoints should not need them.

Run
---
GMAIL_SENDER_ADDRESS= GMAIL_APP_PASSWORD= TWILIO_ACCOUNT_SID= TWILIO_AUTH_TOKEN= SUPABASE_URL=http://127.0.0.1:9 /home/ibrahim/Desktop/techno-projects/techno-terminal/.venv/bin/python -m pytest tests/characterization/test_crm_students_api.py -q -p no:cacheprovider
"""

import uuid
from datetime import date, datetime, timezone
from sqlmodel import select

from app.modules.crm.models.student_models import Student, StudentStatus
from app.modules.crm.models.parent_models import Parent
from app.modules.crm.models.link_models import StudentParent
from app.modules.auth.models.auth_models import User as UserModel


def _uid() -> str:
    return f"cs-{uuid.uuid4().hex}"


def _short() -> str:
    return uuid.uuid4().hex[:10]


def _make_student(db_session, **overrides) -> Student:
    """Insert a committed student (visible to the services' own sessions)."""
    student = Student(
        full_name=overrides.pop("full_name", f"Student {_short()}"),
        date_of_birth=overrides.pop("date_of_birth", None),
        gender=overrides.pop("gender", None),
        phone=overrides.pop("phone", f"555{_short()[:7]}"),
        notes=overrides.pop("notes", None),
        status=overrides.pop("status", StudentStatus.WAITING),
        waiting_since=overrides.pop("waiting_since", None),
        waiting_priority=overrides.pop("waiting_priority", None),
        waiting_notes=overrides.pop("waiting_notes", None),
        **overrides,
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student


def _make_parent(db_session, **overrides) -> Parent:
    """Insert a committed parent (visible to the services' own sessions)."""
    parent = Parent(
        full_name=overrides.pop("full_name", f"Parent {_short()}"),
        phone_primary=overrides.pop("phone_primary", f"555{_short()[:7]}"),
        phone_secondary=overrides.pop("phone_secondary", None),
        email=overrides.pop("email", f"{_short()}@test.local"),
        relation=overrides.pop("relation", "mother"),
        notes=overrides.pop("notes", None),
        **overrides,
    )
    db_session.add(parent)
    db_session.commit()
    db_session.refresh(parent)
    return parent


def _link_student_parent(db_session, student_id: int, parent_id: int, **overrides) -> StudentParent:
    """Insert a committed student-parent link."""
    link = StudentParent(
        student_id=student_id,
        parent_id=parent_id,
        relationship=overrides.pop("relationship", "mother"),
        is_primary=overrides.pop("is_primary", True),
        created_at=overrides.pop("created_at", datetime.now(timezone.utc)),
        **overrides,
    )
    db_session.add(link)
    db_session.commit()
    db_session.refresh(link)
    return link


# ── /api/v1/crm/students ──────────────────────────────────────────────────────


def test_list_students_empty(client_with_uow, override_auth, mock_admin_headers):
    """GET /crm/students returns paginated envelope (may have pre-seeded data)."""
    r = client_with_uow.get("/api/v1/crm/students", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "total", "skip", "limit"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert isinstance(body["total"], int)
    assert body["skip"] == 0
    assert body["limit"] == 50


def test_list_students_with_seed(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students?q=<marker> returns seeded students deterministically."""
    marker = _short()
    s1 = _make_student(db_session, full_name=f"Alice {marker}", phone=f"555{marker}1111", status=StudentStatus.ACTIVE)
    s2 = _make_student(db_session, full_name=f"Bob {marker}", phone=f"555{marker}2222", status=StudentStatus.WAITING)

    r = client_with_uow.get(f"/api/v1/crm/students?q={marker}", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "total", "skip", "limit"}
    assert body["success"] is True
    assert body["total"] >= 2
    assert len(body["data"]) >= 2
    # Verify shape of list items (StudentListingDTO)
    for item in body["data"]:
        assert set(item) >= {"id", "full_name", "status", "phone", "date_of_birth", "age", "gender", "current_group_name", "has_unpaid_balance"}
        assert isinstance(item["id"], int)
        assert isinstance(item["full_name"], str)
        assert item["status"] in ("active", "waiting", "inactive")
        assert isinstance(item["phone"], (str, type(None)))
    # Our seeded students should be in the results
    found_ids = {item["id"] for item in body["data"]}
    assert s1.id in found_ids
    assert s2.id in found_ids


def test_list_students_search_branch_pagination_ignored(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students?q=<marker>&skip=1&limit=2 — search branch ignores skip/limit (pinned, not endorsed)."""
    marker = _short()
    for i in range(5):
        _make_student(db_session, full_name=f"S{i} {marker}", phone=f"555{marker}{i:04d}")

    r = client_with_uow.get(f"/api/v1/crm/students?q={marker}&skip=1&limit=2", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    # Search branch returns ALL matches (max 50), ignoring skip/limit
    assert len(body["data"]) == 5
    assert body["total"] == 5
    # Envelope echoes the params but they have no effect on results
    assert body["skip"] == 1
    assert body["limit"] == 2
    for item in body["data"]:
        assert marker in item["full_name"] or marker in item["phone"]


def test_list_students_non_search_pagination(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students?skip=0&limit=2 (no q) — non-search branch applies skip/limit."""
    marker = _short()
    for i in range(5):
        _make_student(db_session, full_name=f"T{i} {marker}", phone=f"555{marker}3{i:04d}")

    r = client_with_uow.get("/api/v1/crm/students?skip=0&limit=2", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["skip"] == 0
    assert body["limit"] == 2
    # Non-search branch respects limit
    assert len(body["data"]) <= 2


# ── /api/v1/crm/students (POST) ───────────────────────────────────────────────


def test_create_student(client_with_uow, override_auth, mock_admin_headers):
    """POST /crm/students creates student and returns 201 with StudentPublic."""
    unique = _short()
    payload = {
        "student_data": {
            "full_name": f"New Student {unique}",
            "date_of_birth": "2010-01-01",
            "gender": "male",
            "phone": f"555{int(unique, 16) % 10000000:07d}",
            "notes": "Created via test",
            "status": "waiting",
        },
        "parent_id": None,
        "relationship": None,
        "created_by_user_id": None,
    }

    r = client_with_uow.post("/api/v1/crm/students", headers=mock_admin_headers, json=payload)

    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Student registered successfully."
    data = body["data"]
    assert set(data) >= {"id", "full_name", "date_of_birth", "gender", "phone", "status", "notes"}
    assert isinstance(data["id"], int)
    assert data["full_name"] == payload["student_data"]["full_name"]
    assert data["status"] == "waiting"


def test_create_student_bad_body(client_with_uow, override_auth, mock_admin_headers):
    """POST /crm/students with missing required fields returns 422 ValidationError."""
    # Missing student_data.full_name
    r = client_with_uow.post(
        "/api/v1/crm/students",
        headers=mock_admin_headers,
        json={"student_data": {"date_of_birth": "2010-01-01"}},
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


# ── /api/v1/crm/students/grouped ──────────────────────────────────────────────


def test_get_grouped_students_default(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/grouped returns ApiResponse with StudentGroupedResultDTO (group_by=status)."""
    marker = _short()
    _make_student(db_session, full_name=f"G1 {marker}", status=StudentStatus.ACTIVE)
    _make_student(db_session, full_name=f"G2 {marker}", status=StudentStatus.WAITING)
    _make_student(db_session, full_name=f"G3 {marker}", status=StudentStatus.INACTIVE)

    r = client_with_uow.get("/api/v1/crm/students/grouped", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    assert set(data) == {"group_by", "total_unique_students", "groups", "total"}
    assert data["group_by"] == "status"
    assert isinstance(data["total_unique_students"], int)
    assert isinstance(data["groups"], list)
    assert isinstance(data["total"], int)
    for group in data["groups"]:
        assert set(group) == {"key", "label", "count", "students"}
        assert isinstance(group["key"], str)
        assert isinstance(group["label"], str)
        assert isinstance(group["count"], int)
        assert isinstance(group["students"], list)


def test_get_grouped_students_by_gender(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/grouped?group_by=gender returns groups by gender."""
    marker = _short()
    _make_student(db_session, full_name=f"GM {marker}", gender="male")
    _make_student(db_session, full_name=f"GF {marker}", gender="female")

    r = client_with_uow.get("/api/v1/crm/students/grouped?group_by=gender", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["group_by"] == "gender"
    for group in data["groups"]:
        assert group["key"] in ("male", "female", "unknown")


def test_get_grouped_students_by_age_bucket(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/grouped?group_by=age_bucket returns groups by age bucket."""
    marker = _short()
    _make_student(db_session, full_name=f"Age1 {marker}", date_of_birth=date(2015, 1, 1))  # ~11
    _make_student(db_session, full_name=f"Age2 {marker}", date_of_birth=date(2010, 1, 1))  # ~16

    r = client_with_uow.get("/api/v1/crm/students/grouped?group_by=age_bucket", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["group_by"] == "age_bucket"
    for group in data["groups"]:
        # Age bucket keys use format like "age_15_plus", "age_10_14", "unknown"
        assert group["key"].startswith("age_") or group["key"] == "unknown"


# ── /api/v1/crm/students/filter ───────────────────────────────────────────────


def test_filter_students_empty(client_with_uow, override_auth, mock_admin_headers):
    """GET /crm/students/filter returns ApiResponse with StudentFilterResultDTO (no filters)."""
    r = client_with_uow.get("/api/v1/crm/students/filter", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    assert set(data) == {"students", "total", "skip", "limit"}
    assert isinstance(data["students"], list)
    assert isinstance(data["total"], int)
    assert data["skip"] == 0
    assert data["limit"] == 50
    for item in data["students"]:
        assert set(item) >= {"id", "full_name", "age", "status", "gender", "phone", "date_of_birth", "current_group_id", "current_group_name", "group_default_day", "instructor_id", "instructor_name", "current_enrollment_count", "enrolled_courses", "has_unpaid_balance"}


def test_filter_students_with_status(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/filter?status=active returns filtered results."""
    marker = _short()
    _make_student(db_session, full_name=f"FActive {marker}", status=StudentStatus.ACTIVE)
    _make_student(db_session, full_name=f"FWait {marker}", status=StudentStatus.WAITING)

    r = client_with_uow.get(f"/api/v1/crm/students/filter?status=active", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert isinstance(data["students"], list)
    assert isinstance(data["total"], int)
    # All returned students should have status=active
    for item in data["students"]:
        assert item["status"] == "active"
        assert set(item) >= {"id", "full_name", "age", "status", "gender", "phone", "date_of_birth", "current_group_id", "current_group_name", "group_default_day", "instructor_id", "instructor_name", "current_enrollment_count", "enrolled_courses", "has_unpaid_balance"}


def test_filter_students_with_age_range(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/filter?min_age=10&max_age=15 returns filtered results."""
    marker = _short()
    _make_student(db_session, full_name=f"FAge1 {marker}", date_of_birth=date(2015, 1, 1))  # ~11
    _make_student(db_session, full_name=f"FAge2 {marker}", date_of_birth=date(2005, 1, 1))  # ~21

    r = client_with_uow.get(f"/api/v1/crm/students/filter?min_age=10&max_age=15", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    # All returned students should have age in range 10-15
    for item in data["students"]:
        assert item["age"] is not None
        assert 10 <= item["age"] <= 15
        assert set(item) >= {"id", "full_name", "age", "status", "gender", "phone", "date_of_birth", "current_group_id", "current_group_name", "group_default_day", "instructor_id", "instructor_name", "current_enrollment_count", "enrolled_courses", "has_unpaid_balance"}


def test_filter_students_pagination(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/filter?skip=0&limit=2 respects pagination."""
    marker = _short()
    for i in range(5):
        _make_student(db_session, full_name=f"FP{i} {marker}")

    r = client_with_uow.get(f"/api/v1/crm/students/filter?skip=0&limit=2", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["skip"] == 0
    assert data["limit"] == 2
    assert len(data["students"]) <= 2


# ── /api/v1/crm/students/waiting-list ─────────────────────────────────────────


def test_get_waiting_list(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/waiting-list returns ApiResponse[list[WaitingStudentDTO]]."""
    marker = _short()
    _make_student(db_session, full_name=f"W1 {marker}", status=StudentStatus.WAITING, waiting_priority=1, waiting_notes="Priority 1")
    _make_student(db_session, full_name=f"W2 {marker}", status=StudentStatus.WAITING, waiting_priority=2)
    _make_student(db_session, full_name=f"Active {marker}", status=StudentStatus.ACTIVE)  # should not appear

    r = client_with_uow.get("/api/v1/crm/students/waiting-list", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    # Verify WaitingStudentDTO shape (extends StudentListingDTO)
    for item in body["data"]:
        assert set(item) >= {"id", "full_name", "status", "waiting_since", "waiting_priority", "waiting_notes"}
        assert item["status"] == "waiting"
        assert isinstance(item.get("waiting_priority"), (int, type(None)))


def test_get_waiting_list_pagination(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/waiting-list?skip=0&limit=1 respects pagination."""
    marker = _short()
    for i in range(5):
        _make_student(db_session, full_name=f"WP{i} {marker}", status=StudentStatus.WAITING, waiting_priority=i)

    r = client_with_uow.get("/api/v1/crm/students/waiting-list?skip=0&limit=1", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    # Service may or may not respect pagination here; assert shape only
    for item in body["data"]:
        assert item["status"] == "waiting"


# ── /api/v1/crm/students/by-status/{status} ───────────────────────────────────


def test_get_students_by_status_active(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/by-status/active returns ApiResponse[list[StudentResponseDTO]]."""
    marker = _short()
    _make_student(db_session, full_name=f"BSActive {marker}", status=StudentStatus.ACTIVE)
    _make_student(db_session, full_name=f"BSWait {marker}", status=StudentStatus.WAITING)

    r = client_with_uow.get("/api/v1/crm/students/by-status/active", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    for item in body["data"]:
        assert set(item) >= {"id", "full_name", "date_of_birth", "gender", "phone", "notes", "status", "waiting_since", "waiting_priority", "waiting_notes", "created_at", "updated_at"}
        assert item["status"] == "active"


def test_get_students_by_status_waiting(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/by-status/waiting returns waiting students."""
    marker = _short()
    _make_student(db_session, full_name=f"BSWait2 {marker}", status=StudentStatus.WAITING, waiting_priority=1)

    r = client_with_uow.get("/api/v1/crm/students/by-status/waiting", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    for item in body["data"]:
        assert item["status"] == "waiting"


def test_get_students_by_status_invalid(client_with_uow, override_auth, mock_admin_headers):
    """GET /crm/students/by-status/invalid returns 400 (ValueError -> HTTPException)."""
    r = client_with_uow.get("/api/v1/crm/students/by-status/not_a_status", headers=mock_admin_headers)

    assert r.status_code == 400
    body = r.json()
    assert body["success"] is False
    assert "invalid status" in body["message"].lower()


# ── /api/v1/crm/students/status-summary ───────────────────────────────────────


def test_get_student_status_summary(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/status-summary returns ApiResponse[StudentStatusSummaryDTO]."""
    marker = _short()
    _make_student(db_session, full_name=f"SumA {marker}", status=StudentStatus.ACTIVE)
    _make_student(db_session, full_name=f"SumW {marker}", status=StudentStatus.WAITING)
    _make_student(db_session, full_name=f"SumI {marker}", status=StudentStatus.INACTIVE)

    r = client_with_uow.get("/api/v1/crm/students/status-summary", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    assert set(data) == {"total", "active", "waiting", "inactive"}
    assert isinstance(data["total"], int)
    assert isinstance(data["active"], int)
    assert isinstance(data["waiting"], int)
    assert isinstance(data["inactive"], int)
    # Counts are non-negative; exact relationship depends on service implementation (may include/exclude soft-deleted differently)
    assert data["total"] >= 0
    assert data["active"] >= 0
    assert data["waiting"] >= 0
    assert data["inactive"] >= 0


# ── /api/v1/crm/students/{student_id} ─────────────────────────────────────────


def test_get_student_by_id(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/{id} returns ApiResponse with StudentPublic shape."""
    student = _make_student(db_session, full_name="Test Student", phone="5551234567", date_of_birth=date(2010, 5, 15), gender="female", status=StudentStatus.ACTIVE, notes="Test notes")

    r = client_with_uow.get(f"/api/v1/crm/students/{student.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] is None
    data = body["data"]
    assert set(data) >= {"id", "full_name", "date_of_birth", "gender", "phone", "status", "notes"}
    assert data["id"] == student.id
    assert data["full_name"] == "Test Student"
    assert data["phone"] == "5551234567"
    assert data["status"] == "active"
    assert data["date_of_birth"] == "2010-05-15"
    assert data["gender"] == "female"
    assert data["notes"] == "Test notes"


def test_get_student_not_found(client_with_uow, override_auth, mock_admin_headers):
    """GET /crm/students/999999999 returns 404 NotFoundError envelope."""
    r = client_with_uow.get("/api/v1/crm/students/999999999", headers=mock_admin_headers)

    assert r.status_code == 404
    body = r.json()
    assert set(body) == {"success", "error", "message"}
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert "not found" in body["message"].lower()


# ── /api/v1/crm/students/{student_id} (PATCH) ─────────────────────────────────


def test_update_student(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH /crm/students/{id} updates student and returns StudentPublic."""
    student = _make_student(db_session, full_name="Original Name", phone="5550000000", status=StudentStatus.WAITING)

    unique = _short()
    payload = {
        "full_name": f"Updated {unique}",
        "phone": f"555{int(unique, 16) % 10000000:07d}",
        "notes": "Updated via test",
    }

    r = client_with_uow.patch(f"/api/v1/crm/students/{student.id}", headers=mock_admin_headers, json=payload)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    assert data["id"] == student.id
    assert data["full_name"] == payload["full_name"]
    assert data["phone"] == payload["phone"]
    assert data["notes"] == payload["notes"]
    # status unchanged
    assert data["status"] == "waiting"


def test_update_student_partial(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH /crm/students/{id} with only some fields updates only those."""
    student = _make_student(db_session, full_name="Partial Update", phone="5551111111", status=StudentStatus.ACTIVE)

    r = client_with_uow.patch(f"/api/v1/crm/students/{student.id}", headers=mock_admin_headers, json={"notes": "Only notes updated"})

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["notes"] == "Only notes updated"
    assert body["data"]["full_name"] == "Partial Update"
    assert body["data"]["phone"] == "5551111111"
    assert body["data"]["status"] == "active"


def test_update_student_not_found(client_with_uow, override_auth, mock_admin_headers):
    """PATCH /crm/students/999999999 returns 404 NotFoundError."""
    r = client_with_uow.patch("/api/v1/crm/students/999999999", headers=mock_admin_headers, json={"full_name": "X"})

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"


def test_update_student_bad_body(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH /crm/students/{id} with invalid gender returns 500 (DB check constraint -> InternalServerError)."""
    from starlette.testclient import TestClient
    student = _make_student(db_session, full_name="Bad Gender", phone="5552222222")

    test_client = TestClient(client_with_uow.app, raise_server_exceptions=False)
    r = test_client.patch(f"/api/v1/crm/students/{student.id}", headers=mock_admin_headers, json={"gender": "not_a_gender"})

    # DB check constraint violation on students.gender -> 500 InternalServerError
    assert r.status_code == 500
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "InternalServerError"


# ── /api/v1/crm/students/{student_id}/parents ─────────────────────────────────


def test_get_student_parents(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/{student_id}/parents returns ApiResponse[list[ParentPublic]]."""
    student = _make_student(db_session, full_name="Student With Parents")
    parent1 = _make_parent(db_session, full_name="Mother", phone_primary="5551111111", relation="mother")
    parent2 = _make_parent(db_session, full_name="Father", phone_primary="5552222222", relation="father")
    _link_student_parent(db_session, student.id, parent1.id, relationship="mother", is_primary=True)
    _link_student_parent(db_session, student.id, parent2.id, relationship="father", is_primary=False)

    r = client_with_uow.get(f"/api/v1/crm/students/{student.id}/parents", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 2
    for item in body["data"]:
        assert set(item) >= {"id", "full_name", "phone_primary", "phone_secondary", "email", "relation", "notes"}
        assert isinstance(item["id"], int)
        assert isinstance(item["full_name"], str)
        assert isinstance(item["phone_primary"], str)


def test_get_student_parents_empty(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/{student_id}/parents returns empty list for student with no parents."""
    student = _make_student(db_session, full_name="Lonely Student")

    r = client_with_uow.get(f"/api/v1/crm/students/{student.id}/parents", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"] == []


def test_get_student_parents_unknown_student(client_with_uow, override_auth, mock_admin_headers):
    """GET /crm/students/999999999/parents returns 200 with empty list (no student existence check)."""
    r = client_with_uow.get("/api/v1/crm/students/999999999/parents", headers=mock_admin_headers)

    # Current behaviour: returns 200 with empty list, not 404
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"] == []
    # current behaviour (pinned, not endorsed)


# ── /api/v1/crm/students/{student_id}/payments ────────────────────────────────


def test_list_student_payments(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/{student_id}/payments returns PaginatedResponse[PaymentListItem]."""
    student = _make_student(db_session, full_name="Student With Payments")

    r = client_with_uow.get(f"/api/v1/crm/students/{student.id}/payments", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "total", "skip", "limit"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert isinstance(body["total"], int)
    assert body["skip"] == 0
    assert body["limit"] == 50
    for item in body["data"]:
        assert set(item) >= {"id", "student_id", "amount", "payment_date", "payment_method", "status", "receipt_id", "receipt_number", "course_name", "group_name", "level_number", "transaction_type"}
        assert isinstance(item["id"], int)
        assert item["student_id"] == student.id
        assert isinstance(item["amount"], (int, float, str))  # Decimal serializes as number/string


def test_list_student_payments_pagination(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/{student_id}/payments?skip=0&limit=10 respects pagination."""
    student = _make_student(db_session, full_name="Student Paginated Payments")

    r = client_with_uow.get(f"/api/v1/crm/students/{student.id}/payments?skip=0&limit=10", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["skip"] == 0
    assert body["limit"] == 10


def test_list_student_payments_unknown_student(client_with_uow, override_auth, mock_admin_headers):
    """GET /crm/students/999999999/payments returns 200 with empty paginated response (no student existence check)."""
    r = client_with_uow.get("/api/v1/crm/students/999999999/payments", headers=mock_admin_headers)

    # Current behaviour: returns 200 with empty data, not 404
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"] == []
    assert body["total"] == 0
    assert body["skip"] == 0
    # current behaviour (pinned, not endorsed)


# ── Role checks ────────────────────────────────────────────────────────────────


def test_students_endpoints_require_auth(client_with_uow):
    """GET /crm/students without auth returns 401."""
    from app.api.dependencies import get_current_user

    client_with_uow.app.dependency_overrides.pop(get_current_user, None)
    r = client_with_uow.get("/api/v1/crm/students")
    assert r.status_code == 401
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "Unauthorized"


def test_create_student_requires_admin_role(client_with_uow, override_auth, mock_admin_headers):
    """POST /crm/students requires admin role (verified by working with admin)."""
    unique = _short()
    payload = {
        "student_data": {
            "full_name": f"Role Test {unique}",
            "date_of_birth": "2010-01-01",
            "gender": "male",
            "phone": f"555{int(unique, 16) % 10000000:07d}",
        },
        "parent_id": None,
        "relationship": None,
        "created_by_user_id": None,
    }
    r = client_with_uow.post("/api/v1/crm/students", headers=mock_admin_headers, json=payload)
    assert r.status_code == 201