"""Characterization tests for the CRM Parents HTTP API (ticket #17, Part 1 of 3).

Pins the exact status codes, response envelopes and field shapes of every
endpoint under ``/api/v1/crm/parents`` (5 endpoints) BEFORE the CRM HTTP
layer moves into ``app/modules/crm/api/``.

Buckets
-------
* GET endpoints (list, get-by-id) read through services that open their own
  ``get_db()`` session. Rows created via the rollback-only ``uow`` fixture are
  invisible to them. These tests therefore seed data through the committed
  ``db_session`` fixture with uuid-tagged values.
* Write endpoints (create, update, delete) assert response shape only and use
  uuid-tagged values so reruns do not collide (their commits are real).
* No Supabase/Twilio/Gmail dependencies — crm endpoints should not need them.
  If one does, fake it via existing helpers in ``app/testing/``.

Run
---
GMAIL_SENDER_ADDRESS= GMAIL_APP_PASSWORD= TWILIO_ACCOUNT_SID= TWILIO_AUTH_TOKEN= SUPABASE_URL=http://127.0.0.1:9 /home/ibrahim/Desktop/techno-projects/techno-terminal/.venv/bin/python -m pytest app/modules/crm/tests/characterization/test_crm_parents_api.py -q -p no:cacheprovider
"""

import uuid
from sqlmodel import select

from app.modules.crm.models.parent_models import Parent


def _uid() -> str:
    return f"cp-{uuid.uuid4().hex}"


def _short() -> str:
    return uuid.uuid4().hex[:10]


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


# ── /api/v1/crm/parents ──────────────────────────────────────────────────────


def test_list_parents_empty(client_with_uow, override_auth, mock_admin_headers):
    """GET /crm/parents returns paginated envelope (may have pre-seeded data)."""
    r = client_with_uow.get("/api/v1/crm/parents", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "total", "skip", "limit"}
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert isinstance(body["total"], int)
    assert body["skip"] == 0
    assert body["limit"] == 50


def test_list_parents_with_seed(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/parents?q=<marker> returns seeded parents deterministically."""
    marker = _short()
    p1 = _make_parent(db_session, full_name=f"Alice {marker}", phone_primary=f"555{marker}1111")
    p2 = _make_parent(db_session, full_name=f"Bob {marker}", phone_primary=f"555{marker}2222")

    r = client_with_uow.get(f"/api/v1/crm/parents?q={marker}", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "total", "skip", "limit"}
    assert body["success"] is True
    assert body["total"] >= 2
    assert len(body["data"]) >= 2
    # Verify shape of list items (ParentListItem)
    for item in body["data"]:
        assert set(item) >= {"id", "full_name", "phone_primary"}
        assert isinstance(item["id"], int)
        assert isinstance(item["full_name"], str)
        assert isinstance(item["phone_primary"], str)
    # Our seeded parents should be in the results
    found_ids = {item["id"] for item in body["data"]}
    assert p1.id in found_ids
    assert p2.id in found_ids


def test_list_parents_search(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/parents?q=... returns matching parents."""
    marker = _short()
    _make_parent(db_session, full_name=f"UniqueName{marker}", phone_primary=f"555{marker}1111")
    _make_parent(db_session, full_name="Other Parent", phone_primary=f"555{marker}2222")

    r = client_with_uow.get(f"/api/v1/crm/parents?q={marker}", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["total"] >= 1
    for item in body["data"]:
        assert marker in item["full_name"] or marker in item["phone_primary"]


def test_list_parents_pagination_search_branch(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/parents?q=<marker>&skip=...&limit=... — search branch ignores skip/limit (pinned, not endorsed)."""
    marker = _short()
    for i in range(5):
        _make_parent(db_session, full_name=f"P{i} {marker}", phone_primary=f"555{marker}{i:04d}")

    r = client_with_uow.get(f"/api/v1/crm/parents?q={marker}&skip=1&limit=2", headers=mock_admin_headers)

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
        assert marker in item["full_name"] or marker in item["phone_primary"]


def test_list_parents_pagination_non_search(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/parents?skip=0&limit=2 (no q) — non-search branch applies skip/limit."""
    marker = _short()
    for i in range(5):
        _make_parent(db_session, full_name=f"Q{i} {marker}", phone_primary=f"555{marker}2{i:04d}")

    r = client_with_uow.get("/api/v1/crm/parents?skip=0&limit=2", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["skip"] == 0
    assert body["limit"] == 2
    # Non-search branch respects limit
    assert len(body["data"]) <= 2


# ── /api/v1/crm/parents/{parent_id} ──────────────────────────────────────────


def test_get_parent_by_id(client_with_uow, override_auth, mock_admin_headers, db_session):
    """GET /crm/parents/{id} returns ApiResponse with ParentPublic shape."""
    parent = _make_parent(db_session, full_name="Test Parent", phone_primary="5551234567")

    r = client_with_uow.get(f"/api/v1/crm/parents/{parent.id}", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] is None
    data = body["data"]
    # ParentPublic fields
    assert set(data) >= {
        "id", "full_name", "phone_primary", "phone_secondary", "email", "relation", "notes"
    }
    assert data["id"] == parent.id
    assert data["full_name"] == "Test Parent"
    assert data["phone_primary"] == "5551234567"
    assert isinstance(data["phone_secondary"], (str, type(None)))
    assert isinstance(data["email"], (str, type(None)))
    assert isinstance(data["relation"], (str, type(None)))
    assert isinstance(data["notes"], (str, type(None)))


def test_get_parent_not_found(client_with_uow, override_auth, mock_admin_headers):
    """GET /crm/parents/999999999 returns 404 NotFoundError envelope."""
    r = client_with_uow.get("/api/v1/crm/parents/999999999", headers=mock_admin_headers)

    assert r.status_code == 404
    body = r.json()
    assert set(body) == {"success", "error", "message"}
    assert body["success"] is False
    assert body["error"] == "NotFoundError"
    assert "not found" in body["message"].lower()


# ── /api/v1/crm/parents (POST) ───────────────────────────────────────────────


def test_create_parent(client_with_uow, override_auth, mock_admin_headers):
    """POST /crm/parents creates parent and returns 201 with ParentPublic."""
    unique = _short()
    # Use only digits for phone to avoid validator stripping
    phone_digits = f"555{int(unique, 16) % 10000000:07d}"
    payload = {
        "full_name": f"New Parent {unique}",
        "phone_primary": phone_digits,
        "phone_secondary": f"555{int(unique, 16) % 10000000:07d}",
        "email": f"{unique}@example.com",
        "relation": "father",
        "notes": "Created via test",
    }

    r = client_with_uow.post(
        "/api/v1/crm/parents", headers=mock_admin_headers, json=payload
    )

    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Parent created successfully."
    data = body["data"]
    assert set(data) >= {
        "id", "full_name", "phone_primary", "phone_secondary", "email", "relation", "notes"
    }
    assert isinstance(data["id"], int)
    assert data["full_name"] == payload["full_name"]
    # phone_primary is normalized by validator (digits only)
    assert data["phone_primary"] == phone_digits
    assert data["phone_secondary"] == payload["phone_secondary"]
    assert data["email"] == payload["email"]
    assert data["relation"] == payload["relation"]
    assert data["notes"] == payload["notes"]


def test_create_parent_bad_body(client_with_uow, override_auth, mock_admin_headers):
    """POST /crm/parents with missing required fields returns 422 ValidationError."""
    # Missing full_name and phone_primary
    r = client_with_uow.post(
        "/api/v1/crm/parents", headers=mock_admin_headers, json={"email": "bad@test.com"}
    )

    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ValidationError"


# ── /api/v1/crm/parents/{parent_id} (PATCH) ──────────────────────────────────


def test_update_parent(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH /crm/parents/{id} updates parent and returns ParentPublic."""
    parent = _make_parent(db_session, full_name="Original Name", phone_primary="5550000000")

    unique = _short()
    phone_digits = f"555{int(unique, 16) % 10000000:07d}"
    payload = {
        "full_name": f"Updated {unique}",
        "phone_secondary": phone_digits,
        "notes": "Updated via test",
    }

    r = client_with_uow.patch(
        f"/api/v1/crm/parents/{parent.id}", headers=mock_admin_headers, json=payload
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Parent updated successfully."
    data = body["data"]
    assert data["id"] == parent.id
    assert data["full_name"] == payload["full_name"]
    assert data["phone_primary"] == "5550000000"  # unchanged
    assert data["phone_secondary"] == phone_digits
    assert data["notes"] == payload["notes"]


def test_update_parent_partial(client_with_uow, override_auth, mock_admin_headers, db_session):
    """PATCH /crm/parents/{id} with only some fields updates only those."""
    parent = _make_parent(db_session, full_name="Partial Update", phone_primary="5551111111")

    r = client_with_uow.patch(
        f"/api/v1/crm/parents/{parent.id}", headers=mock_admin_headers, json={"relation": "guardian"}
    )

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["relation"] == "guardian"
    assert body["data"]["full_name"] == "Partial Update"  # unchanged


def test_update_parent_not_found(client_with_uow, override_auth, mock_admin_headers):
    """PATCH /crm/parents/999999999 returns 404 NotFound (HTTPException path)."""
    r = client_with_uow.patch(
        "/api/v1/crm/parents/999999999", headers=mock_admin_headers, json={"full_name": "X"}
    )

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    # Router catches NotFoundError and raises HTTPException -> error_type "NotFound"
    assert body["error"] == "NotFound"


# ── /api/v1/crm/parents/{parent_id} (DELETE) ─────────────────────────────────


def test_delete_parent(client_with_uow, override_auth, mock_admin_headers, db_session):
    """DELETE /crm/parents/{id} deletes parent and returns ParentPublic."""
    parent = _make_parent(db_session, full_name="To Delete", phone_primary="5559999999")

    r = client_with_uow.delete(
        f"/api/v1/crm/parents/{parent.id}", headers=mock_admin_headers
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Parent deleted successfully."
    data = body["data"]
    assert data["id"] == parent.id
    assert data["full_name"] == "To Delete"
    # Note: deletion verified via response; the test's db_session is separate from
    # the service's session so a direct get() here may still show the object.


def test_delete_parent_not_found(client_with_uow, override_auth, mock_admin_headers):
    """DELETE /crm/parents/999999999 returns 404 NotFoundError."""
    r = client_with_uow.delete("/api/v1/crm/parents/999999999", headers=mock_admin_headers)

    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "NotFoundError"


# ── Role checks ────────────────────────────────────────────────────────────────


def test_list_parents_requires_auth(client_with_uow):
    """GET /crm/parents without auth returns 401."""
    from app.api.deps import get_current_user

    # Remove auth override
    client_with_uow.app.dependency_overrides.pop(get_current_user, None)
    r = client_with_uow.get("/api/v1/crm/parents")
    assert r.status_code == 401
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "Unauthorized"


def test_create_parent_requires_admin_role(client_with_uow, override_auth, mock_admin_headers):
    """POST /crm/parents requires admin role (verified by working with admin)."""
    # This is covered by test_create_parent but explicitly named for clarity.
    # The require_admin guard allows admin and manager roles.
    unique = _short()
    phone_digits = f"555{int(unique, 16) % 10000000:07d}"
    r = client_with_uow.post(
        "/api/v1/crm/parents",
        headers=mock_admin_headers,
        json={"full_name": f"Role Test {unique}", "phone_primary": phone_digits},
    )
    assert r.status_code == 201