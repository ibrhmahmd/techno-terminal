"""Characterization tests for the auth HTTP API (ticket #15, Phase A).

Pins the exact status codes, response envelopes and field shapes of every
endpoint under ``/api/v1/auth`` (15) and ``/api/v1/admin`` (8) BEFORE the auth
HTTP layer moves into ``app/modules/auth/api``.

Buckets
-------
* Auth services open their own ``get_session()``, so rows created through the
  rollback-only ``uow`` fixture are invisible to them. GET endpoints that need
  data are therefore seeded through the committed ``db_session`` fixture with
  uuid-tagged values. Write endpoints assert response shape only and use
  uuid-tagged values so reruns do not collide (their commits are real).
* Supabase is faked by patching the accessor where the code under test looks it
  up: the router module for login/refresh/logout, the auth service module for
  everything else. No network; nothing here needs the ``supabase`` marker.
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from sqlmodel import select

from app.modules.auth.models.auth_models import User
from app.modules.auth.models.audit_log import AuditLog

# Module that binds get_supabase_anon for login/refresh/logout. This is the only
# string that moves with the router in Phase A.
AUTH_ROUTER = "app.modules.auth.api.auth_router"
AUTH_SERVICE = "app.modules.auth.services.auth_service"


def _uid() -> str:
    return f"ca-{uuid.uuid4().hex}"


def _short() -> str:
    return uuid.uuid4().hex[:10]


def _make_user(db_session, supabase_uid=None, **overrides) -> User:
    """Insert a committed user (visible to the services' own sessions)."""
    user = User(
        username=overrides.pop("username", f"ca_{_short()}"),
        role=overrides.pop("role", "admin"),
        supabase_uid=supabase_uid or _uid(),
        is_active=overrides.pop("is_active", True),
        **overrides,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _seed_audit(db_session, user_id, event_type, count=1) -> None:
    for _ in range(count):
        db_session.add(AuditLog(
            user_id=user_id,
            event_type=event_type,
            ip_address="127.0.0.1",
            user_agent="pytest",
        ))
    db_session.commit()


def _anon_session(uid, access="acc-token", refresh="ref-token"):
    resp = MagicMock()
    resp.session.access_token = access
    resp.session.refresh_token = refresh
    resp.user.id = uid
    return resp


def _fake_admin(uid="sup-uid"):
    admin = MagicMock()
    admin.auth.admin.create_user.return_value.user.id = uid
    return admin


# ── /api/v1/auth ──────────────────────────────────────────────────────────────

def test_login(client_with_uow, db_session):
    uid = _uid()
    user = _make_user(db_session, supabase_uid=uid, last_login=datetime.now(timezone.utc))
    fake = MagicMock()
    fake.auth.sign_in_with_password.return_value = _anon_session(uid, "acc", "ref")

    with patch(f"{AUTH_ROUTER}.get_supabase_anon", return_value=fake):
        r = client_with_uow.post(
            "/api/v1/auth/login",
            json={"email": "x@y.co", "password": "whatever12"},
        )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "Login successful."
    data = body["data"]
    assert set(data) == {"access_token", "refresh_token", "token_type", "user"}
    assert data["access_token"] == "acc"
    assert data["refresh_token"] == "ref"
    assert data["token_type"] == "bearer"
    assert data["user"]["id"] == user.id
    assert data["user"]["role"] == "admin"


def test_refresh(client_with_uow, db_session):
    uid = _uid()
    user = _make_user(db_session, supabase_uid=uid)
    fake = MagicMock()
    fake.auth.refresh_session.return_value = _anon_session(uid, "new-acc", "new-ref")

    with patch(f"{AUTH_ROUTER}.get_supabase_anon", return_value=fake):
        r = client_with_uow.post(
            "/api/v1/auth/refresh", json={"refresh_token": "old-ref"}
        )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["message"] == "Token refreshed."
    assert body["data"]["access_token"] == "new-acc"
    assert body["data"]["refresh_token"] == "new-ref"
    assert body["data"]["user"]["id"] == user.id


def test_logout(client_with_uow):
    fake = MagicMock()
    with patch(f"{AUTH_ROUTER}.get_supabase_anon", return_value=fake):
        r = client_with_uow.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer some-token"},
        )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["data"] is None
    assert body["message"] == "Logged out successfully."
    fake.auth.sign_out.assert_called_once()


def test_me(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.get("/api/v1/auth/me", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    # /me returns a bare UserPublic, not an envelope.
    assert "success" not in body
    assert set(body) >= {"id", "username", "role", "is_active", "employee_id"}
    assert body["role"] == "admin"

    # Drop the auth override so the unauthenticated path is exercised for real.
    from app.api.dependencies import get_current_user

    client_with_uow.app.dependency_overrides.pop(get_current_user, None)
    no_token = client_with_uow.get("/api/v1/auth/me")
    assert no_token.status_code == 401
    assert no_token.json() == {
        "success": False,
        "error": "Unauthorized",
        "message": "Not authenticated",
    }


def test_create_user(client_with_uow, override_auth, mock_admin_headers, db_session):
    username = f"ca_{_short()}"
    fake = _fake_admin(uid=_uid())

    with patch(f"{AUTH_SERVICE}.get_supabase_admin", return_value=fake):
        r = client_with_uow.post(
            "/api/v1/auth/users",
            headers=mock_admin_headers,
            json={
                "employee_id": None,
                "username": username,
                "password": "StrongPassword12",
                "role": "admin",
            },
        )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["message"] == "User account created."
    assert set(body["data"]) >= {"id", "username", "role", "is_active", "employee_id"}
    assert body["data"]["username"] == username
    assert body["data"]["role"] == "admin"
    fake.auth.admin.create_user.assert_called_once()


def test_reset_password(client_with_uow, override_auth, mock_admin_headers, db_session):
    target = _make_user(db_session)
    fake = MagicMock()

    with patch(f"{AUTH_SERVICE}.get_supabase_admin", return_value=fake):
        r = client_with_uow.post(
            f"/api/v1/auth/users/{target.id}/reset-password",
            headers=mock_admin_headers,
            json={"new_password": "ResetPassword12"},
        )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["data"] is None
    assert body["message"] == "Password reset successfully."
    fake.auth.admin.update_user_by_id.assert_called_once()

    short = client_with_uow.post(
        f"/api/v1/auth/users/{target.id}/reset-password",
        headers=mock_admin_headers,
        json={"new_password": "short"},
    )
    assert short.status_code == 422
    assert short.json()["success"] is False
    assert short.json()["error"] == "ValidationError"


def test_change_password(client_with_uow, override_auth, mock_admin_headers):
    anon = MagicMock()
    admin = MagicMock()

    with patch(f"{AUTH_SERVICE}.get_supabase_anon", return_value=anon), patch(
        f"{AUTH_SERVICE}.get_supabase_admin", return_value=admin
    ):
        r = client_with_uow.post(
            "/api/v1/auth/change-password",
            headers=mock_admin_headers,
            json={"current_password": "OldPassword123", "new_password": "NewPassword123"},
        )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["data"] is None
    assert body["message"] == "Password changed successfully."
    anon.auth.sign_in_with_password.assert_called_once()
    admin.auth.admin.update_user_by_id.assert_called_once()

    unauth = client_with_uow.post(
        "/api/v1/auth/change-password",
        json={"current_password": "OldPassword123", "new_password": "NewPassword123"},
    )
    assert unauth.status_code == 401
    assert unauth.json()["success"] is False


def test_forgot_password(client_with_uow):
    anon = MagicMock()
    with patch(f"{AUTH_SERVICE}.get_supabase_anon", return_value=anon):
        r = client_with_uow.post(
            "/api/v1/auth/forgot-password", json={"email": "user@example.com"}
        )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["data"] is None
    assert body["message"] == "If the email exists, a password reset link has been sent."
    anon.auth.reset_password_email.assert_called_once_with("user@example.com")

    empty = client_with_uow.post("/api/v1/auth/forgot-password", json={"email": ""})
    assert empty.status_code == 422
    assert empty.json()["error"] == "ValidationError"


def test_update_profile(client_with_uow, override_auth, mock_admin_headers, db_session):
    # The override user is attached to the fixture's open db_session; the real
    # update_profile service opens its own session, so detach it first.
    current = db_session.exec(
        select(User).where(User.supabase_uid == "test-admin-001")
    ).first()
    original_username = current.username
    db_session.expunge(current)

    new_username = f"ca_{_short()}"
    try:
        r = client_with_uow.patch(
            "/api/v1/auth/me",
            headers=mock_admin_headers,
            json={"username": new_username},
        )

        assert r.status_code == 200
        body = r.json()
        assert set(body) == {"success", "data", "message"}
        assert body["message"] == "Profile updated."
        assert body["data"]["username"] == new_username
        assert body["data"]["role"] == "admin"
    finally:
        # The service committed the rename in its own session, so the shared
        # mock user would keep the new name for every later test. Restore it.
        restored = db_session.exec(
            select(User).where(User.supabase_uid == "test-admin-001")
        ).first()
        if restored is not None and restored.username != original_username:
            restored.username = original_username
            db_session.commit()


def test_list_sessions(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.get("/api/v1/auth/me/sessions", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["data"] == []


def test_me_activity(client_with_uow, override_auth, mock_admin_headers, db_session):
    current = db_session.exec(
        select(User).where(User.supabase_uid == "test-admin-001")
    ).first()
    _seed_audit(db_session, current.id, "login_success")

    r = client_with_uow.get("/api/v1/auth/me/activity", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "total", "skip", "limit"}
    assert isinstance(body["data"], list)
    assert isinstance(body["total"], int)
    assert body["skip"] == 0
    assert body["limit"] == 50
    if body["data"]:
        assert set(body["data"][0]) >= {
            "id", "user_id", "event_type", "ip_address", "user_agent",
            "details", "created_at",
        }


def test_logout_all_sessions(client_with_uow, override_auth, mock_admin_headers):
    admin = MagicMock()
    with patch(f"{AUTH_SERVICE}.get_supabase_admin", return_value=admin):
        r = client_with_uow.post(
            "/api/v1/auth/me/sessions/logout-all", headers=mock_admin_headers
        )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["data"] is None
    assert body["message"] == "All sessions revoked."


def test_mfa_status(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.get("/api/v1/auth/me/mfa/status", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["data"] == {"enrolled": False}


def test_mfa_enroll(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.post("/api/v1/auth/me/mfa/enroll", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["data"] is None
    assert body["message"] == "MFA enrollment is coming soon."


def test_register(client_with_uow, db_session):
    token = _uid()
    _make_user(
        db_session,
        supabase_uid=None,
        username=f"pending_{_short()}",
        is_active=False,
        invite_token=token,
        invite_expires_at=datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=1),
    )
    fake = _fake_admin(uid=_uid())
    username = f"ca_{_short()}"

    with patch(f"{AUTH_SERVICE}.get_supabase_admin", return_value=fake):
        r = client_with_uow.post(
            "/api/v1/auth/register",
            json={"token": token, "username": username, "password": "StrongPassword12"},
        )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["message"] == "Registration complete."
    assert body["data"]["username"] == username
    assert body["data"]["is_active"] is True

    bad = client_with_uow.post(
        "/api/v1/auth/register",
        json={"token": "no-such-token", "username": username, "password": "StrongPassword12"},
    )
    assert bad.status_code == 401
    assert bad.json()["error"] == "AuthError"


# ── /api/v1/admin ─────────────────────────────────────────────────────────────

def test_admin_list_users(client_with_uow, override_system_admin_auth, system_admin_headers, db_session):
    marker = _short()
    _make_user(db_session, username=f"ca_{marker}")

    r = client_with_uow.get(
        "/api/v1/admin/users", params={"q": marker}, headers=system_admin_headers
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "total", "skip", "limit"}
    assert body["total"] == 1
    assert len(body["data"]) == 1
    assert set(body["data"][0]) >= {
        "id", "username", "supabase_uid", "role", "is_active", "employee_id",
    }


def test_admin_get_user(client_with_uow, override_system_admin_auth, system_admin_headers, db_session):
    target = _make_user(db_session)

    r = client_with_uow.get(
        f"/api/v1/admin/users/{target.id}", headers=system_admin_headers
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["data"]["id"] == target.id
    assert body["data"]["username"] == target.username

    missing = client_with_uow.get(
        "/api/v1/admin/users/999999999", headers=system_admin_headers
    )
    assert missing.status_code == 404
    missing_body = missing.json()
    assert set(missing_body) == {"success", "error", "message"}
    assert missing_body["error"] == "NotFoundError"


def test_admin_update_user(client_with_uow, override_system_admin_auth, system_admin_headers, db_session):
    target = _make_user(db_session)

    r = client_with_uow.patch(
        f"/api/v1/admin/users/{target.id}",
        headers=system_admin_headers,
        json={"role": "system_admin"},
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["message"] == "User updated."
    assert body["data"]["id"] == target.id
    assert body["data"]["role"] == "system_admin"


def test_admin_delete_user(client_with_uow, override_system_admin_auth, system_admin_headers, db_session):
    target = _make_user(db_session, supabase_uid=_uid())
    admin = MagicMock()

    with patch(f"{AUTH_SERVICE}.get_supabase_admin", return_value=admin):
        r = client_with_uow.delete(
            f"/api/v1/admin/users/{target.id}", headers=system_admin_headers
        )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["data"] is None
    assert body["message"] == "User deleted."
    admin.auth.admin.delete_user.assert_called_once()


def test_admin_invite_user(client_with_uow, override_system_admin_auth, system_admin_headers):
    email = f"{_short()}@test.local"

    r = client_with_uow.post(
        "/api/v1/admin/users/invite",
        headers=system_admin_headers,
        json={"email": email, "role": "admin", "employee_id": None},
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["message"] == "Invite sent."
    data = body["data"]
    assert set(data) >= {"id", "username", "role", "is_active", "invite_expires_at"}
    assert data["username"] == email
    assert data["is_active"] is False


def test_admin_audit_logins(client_with_uow, override_system_admin_auth, system_admin_headers, db_session):
    target = _make_user(db_session)
    _seed_audit(db_session, target.id, "login_success", count=2)

    r = client_with_uow.get(
        "/api/v1/admin/audit/logins",
        params={"user_id": target.id, "from": "2020-01-01"},
        headers=system_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "total", "skip", "limit"}
    assert body["total"] == 2
    assert len(body["data"]) == 2
    assert set(body["data"][0]) >= {
        "id", "user_id", "event_type", "ip_address", "user_agent", "details",
        "created_at",
    }
    assert body["data"][0]["event_type"] == "login_success"


def test_admin_audit_password_changes(client_with_uow, override_system_admin_auth, system_admin_headers, db_session):
    target = _make_user(db_session)
    _seed_audit(db_session, target.id, "password_change")

    r = client_with_uow.get(
        "/api/v1/admin/audit/password-changes",
        params={"user_id": target.id, "from": "2020-01-01"},
        headers=system_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "total", "skip", "limit"}
    assert body["total"] == 1
    assert body["data"][0]["event_type"] == "password_change"


def test_admin_audit_failed_attempts(client_with_uow, override_system_admin_auth, system_admin_headers, db_session):
    _seed_audit(db_session, _make_user(db_session).id, "login_failure")

    r = client_with_uow.get(
        "/api/v1/admin/audit/failed-attempts",
        params={"from": "2020-01-01"},
        headers=system_admin_headers,
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "total", "skip", "limit"}
    assert isinstance(body["data"], list)
    assert isinstance(body["total"], int)
