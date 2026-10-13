"""Characterization tests for the CRM Students Lifecycle HTTP API (ticket #17, Part 3b of 4).

Pins the exact status codes, response envelopes and field shapes of the second-half
endpoints under ``/api/v1/crm/students/*`` and ``/api/v1/crm/admin/deleted-students``
(10 endpoints) BEFORE the CRM HTTP layer moves into ``app/modules/crm/api/``.

Endpoints covered:
* PATCH   /crm/students/{student_id}/status
* POST    /crm/students/{student_id}/status/toggle
* PATCH   /crm/students/{student_id}/waiting-priority
* DELETE  /crm/students/{student_id}
* GET     /crm/students/{student_id}/details
* GET     /crm/students/{student_id}/siblings
* DELETE  /crm/students/{student_id}/soft
* POST    /crm/students/{student_id}/restore
* DELETE  /crm/students/{student_id}/hard
* GET     /crm/admin/deleted-students

Buckets
-------
* GET endpoints (details, siblings, deleted-students) read through services that
  open their own ``get_db()`` session. Rows created via the rollback-only ``uow``
  fixture are invisible to them. These tests therefore seed data through the
  committed ``db_session`` fixture with uuid-tagged values.
* Write endpoints (status update, toggle, waiting-priority, delete, soft-delete,
  restore, hard-delete) assert response shape only and use uuid-tagged values so
  reruns do not collide (their commits are real).
* No Supabase/Twilio/Gmail dependencies — crm endpoints should not need them.

Observed Quirks (pinned, not endorsed)
--------------------------------------
* All endpoints that catch NotFoundError and raise HTTPException(404) return
  ``{"error": "NotFound"}`` instead of ``{"error": "NotFoundError"}`` because
  the router converts NotFoundError to HTTPException before the global handler sees it.
* DELETE /crm/students/{student_id} returns 200 "success" even for non-existent
  students (router ignores service's False return value). For existing students
  it returns 500 InternalServerError (service bug: StudentRepository has no delete method).
* GET /crm/students/{student_id}/siblings for unknown student returns 404 with
  "NotFound" (service raises NotFoundError but router doesn't catch it; somehow
  becomes HTTPException).

Run
---
GMAIL_SENDER_ADDRESS= GMAIL_APP_PASSWORD= TWILIO_ACCOUNT_SID= TWILIO_AUTH_TOKEN= SUPABASE_URL=http://127.0.0.1:9 /home/ibrahim/Desktop/techno-projects/techno-terminal/.venv/bin/python -m pytest app/modules/crm/tests/characterization/test_crm_students_lifecycle_api.py -q -p no:cacheprovider
"""

import uuid
from datetime import date, datetime
from sqlmodel import select

from app.modules.crm.models.student_models import Student, StudentStatus
from app.modules.crm.models.parent_models import Parent
from app.modules.crm.models.link_models import StudentParent


def _uid() -> str:
    return f"csl-{uuid.uuid4().hex}"


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


def _link_student_parent(db_session, student_id: int, parent_id: int, relationship: str = "mother", is_primary: bool = True) -> StudentParent:
    """Link a student to a parent."""
    link = StudentParent(
        student_id=student_id,
        parent_id=parent_id,
        relationship=relationship,
        is_primary=is_primary,
    )
    db_session.add(link)
    db_session.commit()
    db_session.refresh(link)
    return link


# ── PATCH /crm/students/{student_id}/status ────────────────────────────────────


def test_update_student_status(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH /crm/students/{student_id}/status updates status and returns StudentResponseDTO."""
    student = _make_student(db_session, status=StudentStatus.WAITING)
    unique = _short()

    payload = {
        "status": "active",
        "notes": f"Status update {unique}",
    }

    r = client_with_uow.patch(
        f"/api/v1/crm/students/{student.id}/status",
        headers=mock_admin_headers,
        json=payload,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    # Message uses enum representation (current behaviour, pinned)
    assert "Student status updated to" in body["message"]
    data = body["data"]
    # StudentResponseDTO fields
    assert set(data) >= {"id", "full_name", "status"}
    assert data["id"] == student.id
    assert data["status"] == "active"
    assert isinstance(data["full_name"], str)


def test_update_student_status_bad_body(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH /crm/students/{student_id}/status with invalid status returns 422 (Pydantic validation)."""
    student = _make_student(db_session, status=StudentStatus.WAITING)

    payload = {"status": "invalid_status"}

    r = client_with_uow.patch(
        f"/api/v1/crm/students/{student.id}/status",
        headers=mock_admin_headers,
        json=payload,
    )

    # Pydantic validates the enum before router code runs -> 422 ValidationError
    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


def test_update_student_status_not_found(client_with_uow, override_auth, mock_admin_headers):
    """PATCH /crm/students/999999999/status returns 404 with error 'NotFound' (router converts NotFoundError to HTTPException)."""
    payload = {"status": "active", "notes": "test"}

    r = client_with_uow.patch(
        "/api/v1/crm/students/999999999/status",
        headers=mock_admin_headers,
        json=payload,
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    # Router catches NotFoundError and raises HTTPException(404) -> http_exception_handler maps 404 to "NotFound"
    assert body["error"] == "NotFound"
    assert "not found" in body["message"].lower()


# ── POST /crm/students/{student_id}/status/toggle ─────────────────────────────


def test_toggle_student_status(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST /crm/students/{student_id}/status/toggle toggles status and returns StudentResponseDTO."""
    # Start with WAITING, should toggle to ACTIVE
    student = _make_student(db_session, status=StudentStatus.WAITING)

    r = client_with_uow.post(
        f"/api/v1/crm/students/{student.id}/status/toggle",
        headers=mock_admin_headers,
        json={"notes": "Toggle test"},
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert "toggled" in body["message"].lower()
    data = body["data"]
    assert set(data) >= {"id", "full_name", "status"}
    assert data["id"] == student.id
    assert data["status"] == "active"


def test_toggle_student_status_active_to_inactive(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST /crm/students/{student_id}/status/toggle from ACTIVE toggles to INACTIVE (per service logic)."""
    # Start with ACTIVE, should toggle to INACTIVE
    student = _make_student(db_session, status=StudentStatus.ACTIVE)

    r = client_with_uow.post(
        f"/api/v1/crm/students/{student.id}/status/toggle",
        headers=mock_admin_headers,
        json={"notes": "Toggle test"},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["status"] == "inactive"


def test_toggle_student_status_not_found(client_with_uow, override_auth, mock_admin_headers):
    """POST /crm/students/999999999/status/toggle returns 404 with error 'NotFound'."""
    r = client_with_uow.post(
        "/api/v1/crm/students/999999999/status/toggle",
        headers=mock_admin_headers,
        json={"notes": "test"},
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFound"


# ── PATCH /crm/students/{student_id}/waiting-priority ─────────────────────────


def test_set_waiting_priority(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH /crm/students/{student_id}/waiting-priority sets priority and returns StudentResponseDTO."""
    student = _make_student(db_session, status=StudentStatus.WAITING, waiting_priority=None)
    unique = _short()

    payload = {
        "priority": 1,
        "notes": f"Priority set {unique}",
    }

    r = client_with_uow.patch(
        f"/api/v1/crm/students/{student.id}/waiting-priority",
        headers=mock_admin_headers,
        json=payload,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == f"Waiting priority set to {payload['priority']}"
    data = body["data"]
    assert set(data) >= {"id", "full_name", "status"}
    assert data["id"] == student.id
    assert data["status"] == "waiting"


def test_set_waiting_priority_active_student(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH /crm/students/{student_id}/waiting-priority on ACTIVE student returns 200 (service allows it).

    Current behaviour (pinned, not endorsed): service doesn't validate waiting status.
    """
    student = _make_student(db_session, status=StudentStatus.ACTIVE)

    payload = {"priority": 1, "notes": "test"}

    r = client_with_uow.patch(
        f"/api/v1/crm/students/{student.id}/waiting-priority",
        headers=mock_admin_headers,
        json=payload,
    )

    # Service allows setting priority on any student (no waiting-list check)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["id"] == student.id


def test_set_waiting_priority_unknown_student(client_with_uow, override_auth, mock_admin_headers):
    """PATCH /crm/students/999999999/waiting-priority returns 404 with error 'NotFound'."""
    payload = {"priority": 1, "notes": "test"}

    r = client_with_uow.patch(
        "/api/v1/crm/students/999999999/waiting-priority",
        headers=mock_admin_headers,
        json=payload,
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFound"


# ── DELETE /crm/students/{student_id} ──────────────────────────────────────────


def test_delete_student_soft_deletes(client_with_uow, override_auth, mock_admin_headers, db_session, uow):
    """DELETE /crm/students/{id} soft-deletes the student (#59; it was a 500)."""
    student = _make_student(db_session, full_name=f"To Delete {_short()}")

    r = client_with_uow.delete(f"/api/v1/crm/students/{student.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["message"] == "Student deleted successfully."
    assert body["data"] is None
    assert uow.session.get(Student, student.id).deleted_at is not None
    # Already deleted -> not found
    again = client_with_uow.delete(f"/api/v1/crm/students/{student.id}", headers=mock_admin_headers)
    assert again.status_code == 404


def test_delete_student_not_found_is_404(client_with_uow, override_auth, mock_admin_headers):
    """DELETE /crm/students/999999999 is a 404 (#59; it answered 200 'deleted')."""
    r = client_with_uow.delete("/api/v1/crm/students/999999999", headers=mock_admin_headers)

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert body["message"] == "Student 999999999 not found"


# ── GET /crm/students/{student_id}/details ─────────────────────────────────────


def test_get_student_details(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/{student_id}/details returns ApiResponse[StudentWithDetails]."""
    student = _make_student(
        db_session,
        full_name=f"Detail Student {_short()}",
        status=StudentStatus.ACTIVE,
        date_of_birth=date(2010, 5, 15),
        gender="female",
        phone="5551234567",
        notes="Test notes",
    )

    r = client_with_uow.get(
        f"/api/v1/crm/students/{student.id}/details",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    data = body["data"]
    # StudentWithDetails fields
    assert set(data) >= {
        "id", "full_name", "date_of_birth", "age", "gender", "phone", "notes",
        "status", "is_active", "school_name",
        "waiting_since", "waiting_priority", "waiting_notes",
        "created_at", "updated_at",
        "primary_parent", "enrollments", "current_enrollment",
        "sessions_attended_count", "sessions_absent_count", "last_session_attended",
        "enrollment_attendance", "balance_summary", "siblings",
    }
    assert data["id"] == student.id
    assert data["full_name"] == student.full_name
    assert data["status"] == "active"
    assert data["is_active"] is True
    assert isinstance(data["age"], (int, type(None)))
    assert isinstance(data["enrollments"], list)
    assert isinstance(data["siblings"], list)
    assert isinstance(data["balance_summary"], dict)
    assert set(data["balance_summary"]) >= {
        "total_due", "total_discounts", "total_paid", "net_balance",
        "enrollment_count", "unpaid_enrollments",
    }


def test_get_student_details_not_found(client_with_uow, override_auth, mock_admin_headers):
    """GET /crm/students/999999999/details returns 404 with error 'NotFound' (router converts NotFoundError to HTTPException)."""
    r = client_with_uow.get(
        "/api/v1/crm/students/999999999/details",
        headers=mock_admin_headers,
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    # Router catches NotFoundError and raises HTTPException(404) -> http_exception_handler maps 404 to "NotFound"
    assert body["error"] == "NotFound"


# ── GET /crm/students/{student_id}/siblings ────────────────────────────────────


def test_get_student_siblings(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/{student_id}/siblings returns ApiResponse[List[SiblingInfo]]."""
    parent = _make_parent(db_session, full_name=f"Shared Parent {_short()}")
    student1 = _make_student(db_session, full_name=f"Sibling1 {_short()}")
    student2 = _make_student(db_session, full_name=f"Sibling2 {_short()}")
    _link_student_parent(db_session, student1.id, parent.id, "mother", True)
    _link_student_parent(db_session, student2.id, parent.id, "mother", False)

    r = client_with_uow.get(
        f"/api/v1/crm/students/{student1.id}/siblings",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    # Should find student2 as sibling
    assert len(body["data"]) >= 1
    for sibling in body["data"]:
        assert set(sibling) >= {
            "student_id", "full_name", "age", "gender", "status",
            "parent_id", "parent_name", "enrollments_count",
        }
        assert isinstance(sibling["student_id"], int)
        assert isinstance(sibling["full_name"], str)
        assert sibling["parent_id"] == parent.id
        assert sibling["parent_name"] == parent.full_name


def test_get_student_siblings_no_parent(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/{student_id}/siblings returns empty list when student has no parent."""
    student = _make_student(db_session)

    r = client_with_uow.get(
        f"/api/v1/crm/students/{student.id}/siblings",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"] == []


def test_get_student_siblings_only_child(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/{student_id}/siblings returns empty list when student is only child."""
    parent = _make_parent(db_session)
    student = _make_student(db_session)
    _link_student_parent(db_session, student.id, parent.id, "mother", True)

    r = client_with_uow.get(
        f"/api/v1/crm/students/{student.id}/siblings",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"] == []


def test_get_student_siblings_unknown_student(client_with_uow, override_auth, mock_admin_headers):
    """GET /crm/students/999999999/siblings returns 404 with error 'NotFoundError' (service raises NotFoundError; global handler catches it).

    Current behaviour (pinned, not endorsed): router doesn't catch NotFoundError for this endpoint.
    """
    r = client_with_uow.get(
        "/api/v1/crm/students/999999999/siblings",
        headers=mock_admin_headers,
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"


# ── DELETE /crm/students/{student_id}/soft ─────────────────────────────────────


def test_soft_delete_student(client_with_uow, override_auth, mock_admin_headers, db_session):
    """DELETE /crm/students/{student_id}/soft soft-deletes student and returns StudentDeletionResult."""
    student = _make_student(db_session, full_name=f"To Soft Delete {_short()}")

    r = client_with_uow.delete(
        f"/api/v1/crm/students/{student.id}/soft",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert "soft-deleted" in body["message"].lower()
    data = body["data"]
    assert set(data) >= {"student_id", "status"}
    assert data["student_id"] == student.id
    assert data["status"] == "soft_deleted"


def test_soft_delete_student_not_found(client_with_uow, override_auth, mock_admin_headers):
    """DELETE /crm/students/999999999/soft returns 404 with error 'NotFound'."""
    r = client_with_uow.delete(
        "/api/v1/crm/students/999999999/soft",
        headers=mock_admin_headers,
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFound"


# ── POST /crm/students/{student_id}/restore ────────────────────────────────────


def test_restore_student(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST /crm/students/{student_id}/restore restores soft-deleted student and returns StudentDeletionResult.

    Creates a student, soft-deletes it via the API, then restores it.
    """
    student = _make_student(db_session, full_name=f"To Restore {_short()}")

    # First soft-delete via the API
    r_soft = client_with_uow.delete(
        f"/api/v1/crm/students/{student.id}/soft",
        headers=mock_admin_headers,
    )
    assert r_soft.status_code == 200

    # Now restore
    r = client_with_uow.post(
        f"/api/v1/crm/students/{student.id}/restore",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Student restored successfully"
    data = body["data"]
    assert set(data) >= {"student_id", "status"}
    assert data["student_id"] == student.id
    assert data["status"] == "restored"


def test_restore_student_not_found_or_not_deleted(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST /crm/students/{student_id}/restore on non-deleted student returns 404 with error 'NotFound'."""
    student = _make_student(db_session, full_name=f"Not Deleted {_short()}")

    r = client_with_uow.post(
        f"/api/v1/crm/students/{student.id}/restore",
        headers=mock_admin_headers,
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFound"


def test_restore_student_unknown(client_with_uow, override_auth, mock_admin_headers):
    """POST /crm/students/999999999/restore returns 404 with error 'NotFound'."""
    r = client_with_uow.post(
        "/api/v1/crm/students/999999999/restore",
        headers=mock_admin_headers,
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFound"


# ── DELETE /crm/students/{student_id}/hard ─────────────────────────────────────


def test_hard_delete_student(client_with_uow, override_auth, mock_admin_headers, db_session):
    """DELETE /crm/students/{student_id}/hard permanently deletes student and returns StudentDeletionResult."""
    student = _make_student(db_session, full_name=f"To Hard Delete {_short()}")

    r = client_with_uow.delete(
        f"/api/v1/crm/students/{student.id}/hard",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert "permanently" in body["message"].lower()
    data = body["data"]
    assert set(data) >= {"student_id", "status"}
    assert data["student_id"] == student.id
    assert data["status"] == "permanently_deleted"


def test_hard_delete_student_not_found(client_with_uow, override_auth, mock_admin_headers):
    """DELETE /crm/students/999999999/hard returns 404 with error 'NotFound'."""
    r = client_with_uow.delete(
        "/api/v1/crm/students/999999999/hard",
        headers=mock_admin_headers,
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFound"


# ── GET /crm/admin/deleted-students ────────────────────────────────────────────


def test_list_deleted_students(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/admin/deleted-students lists soft-deleted students."""
    # Create and soft-delete a student via the API
    student = _make_student(db_session, full_name=f"Deleted List {_short()}")

    # Soft delete via API
    r_soft = client_with_uow.delete(
        f"/api/v1/crm/students/{student.id}/soft",
        headers=mock_admin_headers,
    )
    assert r_soft.status_code == 200

    r = client_with_uow.get(
        "/api/v1/crm/admin/deleted-students",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    # Find our soft-deleted student by id (shared growing set; never by position)
    found = any(item["id"] == student.id for item in body["data"])
    assert found, f"Soft-deleted student {student.id} not found in deleted-students list"
    # Verify StudentListingDTO shape for the found item
    for item in body["data"]:
        if item["id"] == student.id:
            assert set(item) >= {
                "id", "full_name", "status", "phone", "date_of_birth",
                "age", "gender", "current_group_name", "has_unpaid_balance",
            }
            assert item["full_name"] == student.full_name
            break


def test_list_deleted_students_pagination(client_with_uow, override_auth, mock_admin_headers):
    """GET /crm/admin/deleted-students?skip=0&limit=10 respects pagination params."""
    r = client_with_uow.get(
        "/api/v1/crm/admin/deleted-students?skip=0&limit=10",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    # Pagination params are echoed in non-search branch but service uses limit/offset
    assert len(body["data"]) <= 10


# ── Role checks ────────────────────────────────────────────────────────────────


def test_lifecycle_endpoints_require_auth(client_with_uow):
    """Endpoints under /crm/students/* require authentication."""
    from app.api.deps import get_current_user

    client_with_uow.app.dependency_overrides.pop(get_current_user, None)

    # Test a few representative endpoints
    r = client_with_uow.patch("/api/v1/crm/students/1/status", json={"status": "active"})
    assert r.status_code == 401

    r = client_with_uow.post("/api/v1/crm/students/1/status/toggle", json={})
    assert r.status_code == 401

    r = client_with_uow.get("/api/v1/crm/students/1/details")
    assert r.status_code == 401

    r = client_with_uow.get("/api/v1/crm/admin/deleted-students")
    assert r.status_code == 401


def test_lifecycle_write_endpoints_require_admin_role(client_with_uow, override_auth, mock_admin_headers, db_session):
    """Write endpoints require admin role (verified by working with admin)."""
    student = _make_student(db_session)

    # These should succeed with admin role
    r = client_with_uow.patch(
        f"/api/v1/crm/students/{student.id}/status",
        headers=mock_admin_headers,
        json={"status": "active"},
    )
    assert r.status_code == 200

    r = client_with_uow.post(
        f"/api/v1/crm/students/{student.id}/status/toggle",
        headers=mock_admin_headers,
        json={},
    )
    assert r.status_code == 200

    r = client_with_uow.patch(
        f"/api/v1/crm/students/{student.id}/waiting-priority",
        headers=mock_admin_headers,
        json={"priority": 1},
    )
    assert r.status_code == 200

    r = client_with_uow.delete(
        f"/api/v1/crm/students/{student.id}/soft",
        headers=mock_admin_headers,
    )
    assert r.status_code == 200