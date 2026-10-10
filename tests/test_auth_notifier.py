"""Tests for AuthNotifier port wiring and behavior (ADR-0007)."""

import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import BackgroundTasks
from sqlmodel import Session, select

from app.modules.auth import AuthNotifier
from app.modules.auth.api.deps import get_auth_notifier as auth_deps_get_auth_notifier
from app.modules.auth.models.auth_models import User
from app.modules.auth.models.audit_log import AuditLog, AuditLogEventType
from app.modules.notifications.adapters import get_auth_notifier as notif_adapters_get_auth_notifier
from app.modules.notifications.services.notification_service import NotificationService
from tests.utils.auth_notifier_fake import FakeAuthNotifier


def _uid() -> str:
    return f"tn-{uuid.uuid4().hex}"


def _make_user(db_session: Session, supabase_uid=None, **overrides) -> User:
    user = User(
        username=overrides.pop("username", f"tn_{uuid.uuid4().hex[:10]}"),
        role=overrides.pop("role", "admin"),
        supabase_uid=supabase_uid or _uid(),
        is_active=overrides.pop("is_active", True),
        last_login=overrides.pop("last_login", None),
        **overrides,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _seed_audit(db_session: Session, user_id: int, event_type: str, **kwargs) -> AuditLog:
    log = AuditLog(
        user_id=user_id,
        event_type=event_type,
        ip_address=kwargs.get("ip_address", "127.0.0.1"),
        user_agent=kwargs.get("user_agent", "pytest"),
        details=kwargs.get("details"),
    )
    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)
    return log


def _anon_session(uid, access="acc-token", refresh="ref-token"):
    resp = MagicMock()
    resp.session.access_token = access
    resp.session.refresh_token = refresh
    resp.user.id = uid
    resp.user.email = "test@example.com"
    return resp


# ── (a) FakeAuthNotifier override: alert raised on first login; no alert on same IP/UA ──

@contextmanager
def _with_fake_notifier(client_with_uow, fake_notifier):
    """Context manager to temporarily override get_auth_notifier and restore original."""
    app = client_with_uow.app
    original = app.dependency_overrides.get(auth_deps_get_auth_notifier)
    app.dependency_overrides[auth_deps_get_auth_notifier] = lambda: fake_notifier
    try:
        yield
    finally:
        if original is not None:
            app.dependency_overrides[auth_deps_get_auth_notifier] = original
        else:
            app.dependency_overrides.pop(auth_deps_get_auth_notifier, None)


def test_login_first_time_triggers_alert(client_with_uow, db_session):
    """First-ever login triggers alert via notifier."""
    uid = _uid()
    user = _make_user(db_session, supabase_uid=uid, last_login=None)
    fake_supabase = MagicMock()
    fake_supabase.auth.sign_in_with_password.return_value = _anon_session(uid)

    fake_notifier = FakeAuthNotifier()

    with _with_fake_notifier(client_with_uow, fake_notifier):
        with patch("app.modules.auth.api.auth_router.get_supabase_anon", return_value=fake_supabase):
            r = client_with_uow.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "whatever12"},
            )

    assert r.status_code == 200
    assert len(fake_notifier.calls) == 1
    call = fake_notifier.calls[0]
    assert call["username"] == user.username
    assert call["alert_reason"] == "First time this user has ever logged in."


def test_login_same_ip_ua_no_alert(client_with_uow, db_session):
    """Login with same IP and UA as last login does not trigger alert."""
    uid = _uid()
    user = _make_user(db_session, supabase_uid=uid, last_login=datetime.now(timezone.utc))
    # TestClient uses "testclient" for both host and user-agent
    _seed_audit(db_session, user.id, AuditLogEventType.LOGIN_SUCCESS, ip_address="testclient", user_agent="testclient")

    fake_supabase = MagicMock()
    fake_supabase.auth.sign_in_with_password.return_value = _anon_session(uid)

    fake_notifier = FakeAuthNotifier()

    with _with_fake_notifier(client_with_uow, fake_notifier):
        with patch("app.modules.auth.api.auth_router.get_supabase_anon", return_value=fake_supabase):
            r = client_with_uow.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "whatever12"},
            )

    assert r.status_code == 200
    assert len(fake_notifier.calls) == 0


def test_login_new_ip_triggers_alert(client_with_uow, db_session):
    """Login from a new IP triggers alert."""
    uid = _uid()
    user = _make_user(db_session, supabase_uid=uid, last_login=datetime.now(timezone.utc))
    # TestClient uses "testclient" for user-agent
    _seed_audit(db_session, user.id, AuditLogEventType.LOGIN_SUCCESS, ip_address="192.168.1.1", user_agent="testclient")

    fake_supabase = MagicMock()
    fake_supabase.auth.sign_in_with_password.return_value = _anon_session(uid)

    fake_notifier = FakeAuthNotifier()

    with _with_fake_notifier(client_with_uow, fake_notifier):
        with patch("app.modules.auth.api.auth_router.get_supabase_anon", return_value=fake_supabase):
            r = client_with_uow.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "whatever12"},
            )

    assert r.status_code == 200
    assert len(fake_notifier.calls) == 1
    assert "new IP address" in fake_notifier.calls[0]["alert_reason"]


def test_login_new_user_agent_triggers_alert(client_with_uow, db_session):
    """Login from a new user agent triggers alert."""
    uid = _uid()
    user = _make_user(db_session, supabase_uid=uid, last_login=datetime.now(timezone.utc))
    # TestClient uses "testclient" for host
    _seed_audit(db_session, user.id, AuditLogEventType.LOGIN_SUCCESS, ip_address="testclient", user_agent="Mozilla/5.0")

    fake_supabase = MagicMock()
    fake_supabase.auth.sign_in_with_password.return_value = _anon_session(uid)

    fake_notifier = FakeAuthNotifier()

    with _with_fake_notifier(client_with_uow, fake_notifier):
        with patch("app.modules.auth.api.auth_router.get_supabase_anon", return_value=fake_supabase):
            r = client_with_uow.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "whatever12"},
            )

    assert r.status_code == 200
    assert len(fake_notifier.calls) == 1
    assert "new device/browser" in fake_notifier.calls[0]["alert_reason"]


# ── (b) Notifier called AFTER commit (audit row visible) ──

def test_notifier_called_after_commit(client_with_uow, db_session):
    """Notifier is invoked only AFTER UnitOfWork.commit() returns.

    Uses an event log to prove ordering: every commit appends "commit",
    notifier call appends "notify". The test asserts the notify index is
    greater than the last commit index.
    """
    from app.db.uow import UnitOfWork

    uid = _uid()
    user = _make_user(db_session, supabase_uid=uid, last_login=None)
    fake_supabase = MagicMock()
    fake_supabase.auth.sign_in_with_password.return_value = _anon_session(uid)

    events: list[str] = []

    # Patch UnitOfWork.commit to record "commit" then call original
    original_commit = UnitOfWork.commit

    def tracking_commit(self):
        events.append("commit")
        return original_commit(self)

    fake_notifier = FakeAuthNotifier()

    def hooked_admin_login(**kwargs):
        events.append("notify")

    fake_notifier.admin_login = hooked_admin_login

    with _with_fake_notifier(client_with_uow, fake_notifier):
        with patch("app.modules.auth.api.auth_router.get_supabase_anon", return_value=fake_supabase):
            with patch.object(UnitOfWork, "commit", side_effect=tracking_commit, autospec=True):
                r = client_with_uow.post(
                    "/api/v1/auth/login",
                    json={"email": "test@example.com", "password": "whatever12"},
                )

    assert r.status_code == 200
    assert len(events) >= 2, f"expected commit + notify events, got {events}"
    assert events.count("notify") == 1, "notifier should be called exactly once"

    # Verify ordering: notify happens after the last commit
    last_commit_idx = max(i for i, e in enumerate(events) if e == "commit")
    notify_idx = events.index("notify")
    assert notify_idx > last_commit_idx, (
        f"notifier called before commit: events={events}, "
        f"last_commit={last_commit_idx}, notify={notify_idx}"
    )


# ── (c) Notifier failure does not fail the login ──

def test_notifier_failure_does_not_fail_login(client_with_uow, db_session):
    """A notifier that raises still allows the login to succeed (200)."""
    uid = _uid()
    user = _make_user(db_session, supabase_uid=uid, last_login=None)
    fake_supabase = MagicMock()
    fake_supabase.auth.sign_in_with_password.return_value = _anon_session(uid)

    fake_notifier = FakeAuthNotifier(should_raise=True, raise_exception=RuntimeError("SMTP down"))

    with _with_fake_notifier(client_with_uow, fake_notifier):
        with patch("app.modules.auth.api.auth_router.get_supabase_anon", return_value=fake_supabase):
            r = client_with_uow.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "whatever12"},
            )

    assert r.status_code == 200
    assert r.json()["message"] == "Login successful."


# ── (d) Real wiring via create_app() schedules notification ──

def test_real_wiring_schedules_notification(client_with_uow, db_session):
    """With real create_app() wiring, login schedules notification via BackgroundTasks."""
    uid = _uid()
    user = _make_user(db_session, supabase_uid=uid, last_login=None)
    fake_supabase = MagicMock()
    fake_supabase.auth.sign_in_with_password.return_value = _anon_session(uid)

    # Use the real app (client_with_uow fixture uses create_app() which has the override)
    # Patch NotificationService.notify_admin_login to verify it's called with BackgroundTasks
    with patch("app.modules.notifications.services.notification_service.NotificationService.notify_admin_login") as mock_notify:
        with patch("app.modules.auth.api.auth_router.get_supabase_anon", return_value=fake_supabase):
            r = client_with_uow.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "whatever12"},
            )

    assert r.status_code == 200
    mock_notify.assert_called_once()
    args, kwargs = mock_notify.call_args
    assert "background_tasks" in kwargs
    assert isinstance(kwargs["background_tasks"], BackgroundTasks)
    assert kwargs["username"] == user.username
    assert kwargs["alert_reason"] == "First time this user has ever logged in."