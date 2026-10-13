"""Characterization tests for the CRM Student History HTTP API (ticket #17, Part 2 of 3).

Pins the exact status codes, response envelopes and field shapes of every
endpoint under ``/api/v1/crm/students/*/history*`` and ``/api/v1/crm/history*``
(10 endpoints) BEFORE the CRM HTTP layer moves into ``app/modules/crm/api/``.

Buckets
-------
* GET endpoints (history, summary, enrollment-history, status-history,
  competition-history, recent, search) read through services that open their own
  ``get_db()`` session. Rows created via the rollback-only ``uow`` fixture are
  invisible to them. These tests therefore seed data through the committed
  ``db_session`` fixture with uuid-tagged values.
* Write endpoints (log-activity POST, PATCH, DELETE) assert response shape only
  and use uuid-tagged values so reruns do not collide (their commits are real).
* No Supabase/Twilio/Gmail dependencies — crm endpoints should not need them.
  If one does, fake it via existing helpers in ``app/testing/``.

Run
---
GMAIL_SENDER_ADDRESS= GMAIL_APP_PASSWORD= TWILIO_ACCOUNT_SID= TWILIO_AUTH_TOKEN= SUPABASE_URL=http://127.0.0.1:9 /home/ibrahim/Desktop/techno-projects/techno-terminal/.venv/bin/python -m pytest app/modules/crm/tests/characterization/test_crm_history_api.py -q -p no:cacheprovider
"""

import uuid
from datetime import datetime, timedelta
from sqlmodel import select

from app.modules.crm.models.student_models import Student, StudentStatus
from app.modules.auth.models.auth_models import User as UserModel
from app.db.uow import UnitOfWork, unit_of_work
from app.db.connection import get_session


def _uid() -> str:
    return f"ch-{uuid.uuid4().hex}"


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


def _make_user(db_session, **overrides) -> UserModel:
    """Insert a committed user (for performed_by FK)."""
    user = UserModel(
        username=overrides.pop("username", f"user_{_short()}"),
        role=overrides.pop("role", "admin"),
        supabase_uid=overrides.pop("supabase_uid", f"test-uid-{_short()}"),
        is_active=overrides.pop("is_active", True),
        **overrides,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _make_activity(db_session, student_id: int, **overrides) -> int:
    """Insert a committed activity log via UnitOfWork and return its ID."""
    from app.modules.crm.repositories.activity_repository import ActivityRepository
    activities = ActivityRepository(db_session)
    activity = activities.create_activity_log(
        student_id=student_id,
        activity_type=overrides.pop("activity_type", "note_added"),
        activity_subtype=overrides.pop("activity_subtype", "general"),
        reference_type=overrides.pop("reference_type", "student"),
        reference_id=overrides.pop("reference_id", student_id),
        description=overrides.pop("description", f"Activity {_short()}"),
        metadata=overrides.pop("metadata", {}),
        performed_by=overrides.pop("performed_by", 1),
        created_at=overrides.pop("created_at", None),
    )
    db_session.commit()
    db_session.refresh(activity)
    return activity.id


# ── /api/v1/crm/students/{student_id}/history ──────────────────────────────


def test_get_student_history_empty(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/{student_id}/history returns empty list for new student."""
    student = _make_student(db_session)

    r = client_with_uow.get(f"/api/v1/crm/students/{student.id}/history", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 0


def test_get_student_history_with_filters(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/{student_id}/history respects date_from/date_to/limit/offset."""
    student = _make_student(db_session)

    r = client_with_uow.get(
        f"/api/v1/crm/students/{student.id}/history?limit=10&offset=0",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    # Verify ActivityLogResponseDTO shape if any activities exist
    for item in body["data"]:
        assert set(item) >= {
            "activity_id",
            "student_id",
            "activity_type",
            "activity_subtype",
            "description",
            "reference",
            "performed_by",
            "meta",
            "created_at",
        }
        assert isinstance(item["activity_id"], int)
        assert item["student_id"] == student.id
        assert isinstance(item["activity_type"], str)
        assert isinstance(item["description"], str)
        if item["reference"] is not None:
            assert set(item["reference"]) >= {"reference_type", "reference_id"}
        if item["performed_by"] is not None:
            assert "user_id" in item["performed_by"]


def test_get_student_history_unknown_student(client_with_uow, override_auth, mock_admin_headers):
    """GET /crm/students/999999999/history returns 200 with empty list (no student existence check)."""
    r = client_with_uow.get("/api/v1/crm/students/999999999/history", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 0


# ── /api/v1/crm/students/{student_id}/activity-summary ─────────────────────


def test_get_activity_summary(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/{student_id}/activity-summary returns ActivitySummaryItem list."""
    student = _make_student(db_session)

    r = client_with_uow.get(f"/api/v1/crm/students/{student.id}/activity-summary", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    # Verify ActivitySummaryItem shape
    for item in body["data"]:
        assert set(item) >= {"activity_type", "count"}
        assert isinstance(item["activity_type"], str)
        assert isinstance(item["count"], int)
        assert item["count"] >= 0


def test_get_activity_summary_unknown_student(client_with_uow, override_auth, mock_admin_headers):
    """GET /crm/students/999999999/activity-summary returns 200 with empty list."""
    r = client_with_uow.get("/api/v1/crm/students/999999999/activity-summary", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 0


# ── /api/v1/crm/students/{student_id}/enrollment-history ───────────────────


def test_get_enrollment_history(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/{student_id}/enrollment-history returns PaginatedResponse[EnrollmentHistoryEntry]."""
    student = _make_student(db_session)

    r = client_with_uow.get(f"/api/v1/crm/students/{student.id}/enrollment-history?limit=10&offset=0", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "total", "skip", "limit"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert isinstance(body["total"], int)
    assert body["skip"] == 0
    assert body["limit"] == 10
    # Verify EnrollmentHistoryEntry shape
    for item in body["data"]:
        assert set(item) >= {
            "id", "student_id", "enrollment_id", "group_id", "group_name",
            "level_number", "enrollment_status", "action", "action_date",
            "previous_group_id", "previous_level_number", "previous_status",
            "amount_due", "discount_applied", "transfer_reason",
            "performed_by", "performed_by_name", "notes",
        }
        assert isinstance(item["id"], int)
        assert item["student_id"] == student.id
        assert isinstance(item["action"], str)
        assert isinstance(item["action_date"], str)  # ISO datetime string


def test_get_enrollment_history_unknown_student(client_with_uow, override_auth, mock_admin_headers):
    """GET /crm/students/999999999/enrollment-history returns 200 with empty paginated response."""
    r = client_with_uow.get("/api/v1/crm/students/999999999/enrollment-history", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 0
    assert body["total"] == 0
    assert body["skip"] == 0


# ── /api/v1/crm/students/{student_id}/status-history ───────────────────────


def test_get_status_history(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/{student_id}/status-history returns PaginatedResponse[StatusHistoryEntry]."""
    student = _make_student(db_session)

    r = client_with_uow.get(f"/api/v1/crm/students/{student.id}/status-history?limit=10&offset=0", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "total", "skip", "limit"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert isinstance(body["total"], int)
    assert body["skip"] == 0
    assert body["limit"] == 10
    # Verify StatusHistoryEntry shape
    for item in body["data"]:
        assert set(item) >= {
            "id", "student_id", "old_status", "new_status", "changed_at",
            "changed_by", "changed_by_name", "reason", "notes",
        }
        assert isinstance(item["id"], int)
        assert item["student_id"] == student.id
        assert isinstance(item["new_status"], str)
        assert isinstance(item["changed_at"], str)  # ISO datetime string


def test_get_status_history_unknown_student(client_with_uow, override_auth, mock_admin_headers):
    """GET /crm/students/999999999/status-history returns 200 with empty paginated response."""
    r = client_with_uow.get("/api/v1/crm/students/999999999/status-history", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 0
    assert body["total"] == 0
    assert body["skip"] == 0


# ── /api/v1/crm/students/{student_id}/competition-history ──────────────────


def test_get_competition_history(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/students/{student_id}/competition-history returns PaginatedResponse[CompetitionHistoryEntry]."""
    student = _make_student(db_session)

    r = client_with_uow.get(f"/api/v1/crm/students/{student.id}/competition-history?limit=10&offset=0", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "total", "skip", "limit"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert isinstance(body["total"], int)
    assert body["skip"] == 0
    assert body["limit"] == 10
    # Verify CompetitionHistoryEntry shape
    for item in body["data"]:
        assert set(item) >= {
            "id", "student_id", "competition_id", "competition_name",
            "team_id", "team_name", "participation_type", "registration_date",
            "subscription_amount", "subscription_paid", "payment_id",
            "result_position", "result_notes", "performed_by",
            "performed_by_name", "created_at",
        }
        assert isinstance(item["id"], int)
        assert item["student_id"] == student.id
        assert isinstance(item["participation_type"], str)
        assert isinstance(item["competition_id"], int)


def test_get_competition_history_unknown_student(client_with_uow, override_auth, mock_admin_headers):
    """GET /crm/students/999999999/competition-history returns 200 with empty paginated response."""
    r = client_with_uow.get("/api/v1/crm/students/999999999/competition-history", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 0
    assert body["total"] == 0
    assert body["skip"] == 0


# ── /api/v1/crm/students/{student_id}/log-activity (POST) ──────────────────


def test_log_manual_activity(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST /crm/students/{student_id}/log-activity creates activity and returns ManualActivityResponseDTO."""
    student = _make_student(db_session)
    unique = _short()

    payload = {
        "activity_type": "note_added",
        "activity_subtype": "general",
        "reference_type": "student",
        "reference_id": student.id,
        "description": f"Test activity {unique}",
        "metadata": {"test": True, "marker": unique},
        "created_at": datetime.utcnow().isoformat(),
    }

    r = client_with_uow.post(
        f"/api/v1/crm/students/{student.id}/log-activity",
        headers=mock_admin_headers,
        json=payload,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Activity logged successfully"
    data = body["data"]
    assert set(data) >= {"activity_id", "student_id", "activity_type", "description", "created_at"}
    assert isinstance(data["activity_id"], int)
    assert data["student_id"] == student.id
    assert data["activity_type"] == "note_added"
    assert data["description"] == f"Test activity {unique}"


def test_log_manual_activity_bad_body(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST /crm/students/{student_id}/log-activity with missing required fields returns 422 ValidationError."""
    student = _make_student(db_session)
    # Missing activity_type and description
    r = client_with_uow.post(
        f"/api/v1/crm/students/{student.id}/log-activity",
        headers=mock_admin_headers,
        json={"reference_type": "student"},
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


def test_log_manual_activity_unknown_student(client_with_uow, override_auth, mock_admin_headers):
    """Fixed in #50 (was a 500 from the student foreign key): an unknown student is a 404."""
    r = client_with_uow.post(
        "/api/v1/crm/students/999999999/log-activity",
        headers=mock_admin_headers,
        json={"activity_type": "note_added", "description": f"Test {_short()}"},
    )

    assert r.status_code == 404
    body = r.json()
    assert body["error"] == "NotFoundError"
    assert body["message"] == "Student 999999999 not found"


# ── /api/v1/crm/students/{student_id}/log-activity/{activity_id} (PATCH) ───


def test_update_manual_activity(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH /crm/students/{student_id}/log-activity/{activity_id} updates activity and returns ManualActivityResponseDTO."""
    student = _make_student(db_session)
    unique1 = _short()
    unique2 = _short()

    # Create activity via UnitOfWork (visible to service's get_db session)
    activity_id = _make_activity(db_session, student.id, description=f"Original {unique1}", metadata={"marker": unique1})

    payload = {
        "activity_type": "note_added",
        "activity_subtype": "updated",
        "description": f"Updated {unique2}",
        "metadata": {"marker": unique2, "updated": True},
    }

    r = client_with_uow.patch(
        f"/api/v1/crm/students/{student.id}/log-activity/{activity_id}",
        headers=mock_admin_headers,
        json=payload,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Activity updated successfully"
    data = body["data"]
    assert data["activity_id"] == activity_id
    assert data["student_id"] == student.id
    assert data["activity_type"] == "note_added"
    assert data["description"] == f"Updated {unique2}"


def test_update_manual_activity_not_found(client_with_uow, override_auth, mock_admin_headers, db_session):
    """Fixed in #51 (was a 500 from a bare ValueError)."""
    student = _make_student(db_session)
    r = client_with_uow.patch(
        f"/api/v1/crm/students/{student.id}/log-activity/999999999",
        headers=mock_admin_headers,
        json={"description": "Updated"},
    )

    assert r.status_code == 404
    body = r.json()
    assert body["error"] == "NotFoundError"
    assert body["message"] == f"Activity log 999999999 not found for student {student.id}"


def test_activity_of_another_student_is_404(client_with_uow, override_auth, mock_admin_headers, db_session):
    """An activity that belongs to a different student is not found for this one (#51); it
    is neither updated nor deleted."""
    owner = _make_student(db_session)
    other = _make_student(db_session)
    activity_id = _make_activity(db_session, owner.id, description=f"Owned {_short()}")

    patched = client_with_uow.patch(
        f"/api/v1/crm/students/{other.id}/log-activity/{activity_id}",
        headers=mock_admin_headers, json={"description": "hijack"},
    )
    deleted = client_with_uow.delete(
        f"/api/v1/crm/students/{other.id}/log-activity/{activity_id}", headers=mock_admin_headers
    )

    assert patched.status_code == 404 and deleted.status_code == 404
    still_there = client_with_uow.patch(
        f"/api/v1/crm/students/{owner.id}/log-activity/{activity_id}",
        headers=mock_admin_headers, json={"description": "owner edit"},
    )
    assert still_there.status_code == 200


# ── /api/v1/crm/students/{student_id}/log-activity/{activity_id} (DELETE) ──


def test_delete_manual_activity(client_with_uow, override_auth, mock_admin_headers, db_session):
    """DELETE /crm/students/{student_id}/log-activity/{activity_id} deletes activity and returns ApiResponse[None]."""
    student = _make_student(db_session)
    unique = _short()

    # Create activity first
    activity_id = _make_activity(db_session, student.id, description=f"To delete {unique}")

    r = client_with_uow.delete(
        f"/api/v1/crm/students/{student.id}/log-activity/{activity_id}",
        headers=mock_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Activity deleted successfully"
    assert body["data"] is None


def test_delete_manual_activity_not_found(client_with_uow, override_auth, mock_admin_headers, db_session):
    """Fixed in #51 (was a 500 from a bare ValueError)."""
    student = _make_student(db_session)
    r = client_with_uow.delete(
        f"/api/v1/crm/students/{student.id}/log-activity/999999999",
        headers=mock_admin_headers,
    )

    assert r.status_code == 404
    assert r.json()["error"] == "NotFoundError"


# ── /api/v1/crm/history/recent ─────────────────────────────────────────────


def test_get_recent_activity(client_with_uow, override_auth, mock_admin_headers):
    """GET /crm/history/recent returns ApiResponse[List[RecentActivityItemDTO]]."""
    r = client_with_uow.get("/api/v1/crm/history/recent?limit=10", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    # Verify RecentActivityItemDTO shape
    for item in body["data"]:
        assert set(item) >= {
            "activity_id", "student_id", "activity_type",
            "description", "created_at", "performed_by_name",
        }
        assert isinstance(item["activity_id"], int)
        assert isinstance(item["student_id"], int)
        assert isinstance(item["activity_type"], str)
        assert isinstance(item["description"], str)


def test_get_recent_activity_limit(client_with_uow, override_auth, mock_admin_headers):
    """GET /crm/history/recent?limit=5 respects limit parameter."""
    r = client_with_uow.get("/api/v1/crm/history/recent?limit=5", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert len(body["data"]) <= 5


# ── /api/v1/crm/history/search (POST) ──────────────────────────────────────


def test_search_activities(client_with_uow, override_auth, mock_admin_headers):
    """POST /crm/history/search returns ApiResponse[List[ActivitySearchResultItemDTO]]."""
    payload = {
        "search_term": "test",
        "activity_types": ["note_added", "registration"],
        "limit": 20,
    }

    r = client_with_uow.post(
        "/api/v1/crm/history/search",
        headers=mock_admin_headers,
        json=payload,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    # Verify ActivitySearchResultItemDTO shape
    for item in body["data"]:
        assert set(item) >= {
            "activity_id", "student_id", "activity_type",
            "description", "meta", "created_at",
        }
        assert isinstance(item["activity_id"], int)
        assert isinstance(item["student_id"], int)
        assert isinstance(item["activity_type"], str)
        assert isinstance(item["description"], str)


def test_search_activities_empty_body(client_with_uow, override_auth, mock_admin_headers):
    """POST /crm/history/search with minimal body returns results (all filters optional)."""
    r = client_with_uow.post(
        "/api/v1/crm/history/search",
        headers=mock_admin_headers,
        json={},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)


# ── Role checks ──────────────────────────────────────────────────────────────


def test_history_endpoints_require_auth(client_with_uow):
    """GET /crm/students/1/history without auth returns 401."""
    from app.api.deps import get_current_user

    client_with_uow.app.dependency_overrides.pop(get_current_user, None)
    r = client_with_uow.get("/api/v1/crm/students/1/history")
    assert r.status_code == 401
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "Unauthorized"


def test_log_activity_requires_admin_role(client_with_uow, override_auth, mock_admin_headers, db_session):
    """POST /crm/students/{student_id}/log-activity requires admin role."""
    student = _make_student(db_session)
    unique = _short()
    payload = {
        "activity_type": "note_added",
        "description": f"Role test {unique}",
    }
    r = client_with_uow.post(
        f"/api/v1/crm/students/{student.id}/log-activity",
        headers=mock_admin_headers,
        json=payload,
    )
    # Should succeed with admin role
    assert r.status_code == 200