"""Tests for AuthService.evaluate_login_alert."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from app.modules.auth.models.auth_models import User
from app.modules.auth.models.audit_log import AuditLog
from app.modules.auth.services.auth_service import AuthService
from app.modules.auth.services.audit_service import AuditService


def _make_user(uow, **overrides) -> User:
    """Create a user in the uow session without explicit ID."""
    user = User(
        username=overrides.pop("username", "testuser"),
        role=overrides.pop("role", "admin"),
        supabase_uid=overrides.pop("supabase_uid", "uid-test"),
        is_active=overrides.pop("is_active", True),
        last_login=overrides.pop("last_login", None),
        **overrides,
    )
    uow.session.add(user)
    uow.session.flush()
    return user


def _make_audit_log(uow, user_id, **overrides) -> AuditLog:
    """Create an audit log in the uow session."""
    log = AuditLog(
        user_id=user_id,
        event_type=overrides.pop("event_type", "login_success"),
        ip_address=overrides.pop("ip_address", "127.0.0.1"),
        user_agent=overrides.pop("user_agent", "test-agent"),
        **overrides,
    )
    uow.session.add(log)
    uow.session.flush()
    return log


class TestEvaluateLoginAlert:
    """Tests for evaluate_login_alert method."""

    def test_first_time_login_returns_alert(self, uow):
        """User with no last_login returns 'first time' alert."""
        auth_svc = AuthService(uow)
        user = _make_user(uow, username="newuser", last_login=None)

        alert = auth_svc.evaluate_login_alert(user, "127.0.0.1", "test-agent")

        assert alert == "First time this user has ever logged in."

    def test_first_login_of_day_returns_alert(self, uow):
        """User whose last_login was yesterday returns 'first login of day' alert."""
        auth_svc = AuthService(uow)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        user = _make_user(uow, username="dailyuser", last_login=yesterday)

        alert = auth_svc.evaluate_login_alert(user, "127.0.0.1", "test-agent")

        assert alert == "First login of the day for this user."

    def test_new_ip_address_returns_alert(self, uow):
        """Login from different IP than last audit log returns new IP alert."""
        auth_svc = AuthService(uow)
        user = _make_user(uow, username="ipuser", last_login=datetime.now(timezone.utc))
        _make_audit_log(uow, user.id, ip_address="192.168.1.100", user_agent="old-agent")

        alert = auth_svc.evaluate_login_alert(user, "10.0.0.1", "test-agent")

        assert alert == "Login from a new IP address (Previous: 192.168.1.100)."

    def test_new_device_browser_returns_alert(self, uow):
        """Login from different user_agent than last audit log returns new device alert."""
        auth_svc = AuthService(uow)
        user = _make_user(uow, username="deviceuser", last_login=datetime.now(timezone.utc))
        _make_audit_log(uow, user.id, ip_address="127.0.0.1", user_agent="old-browser")

        alert = auth_svc.evaluate_login_alert(user, "127.0.0.1", "new-browser")

        assert alert == "Login from a new device/browser."

    def test_same_ip_and_ua_returns_none(self, uow):
        """Same IP and user_agent as last audit log returns no alert."""
        auth_svc = AuthService(uow)
        user = _make_user(uow, username="sameuser", last_login=datetime.now(timezone.utc))
        _make_audit_log(uow, user.id, ip_address="127.0.0.1", user_agent="same-agent")

        alert = auth_svc.evaluate_login_alert(user, "127.0.0.1", "same-agent")

        assert alert is None

    def test_no_audit_log_returns_none_when_last_login_today(self, uow):
        """No audit log but last_login is today returns no alert."""
        auth_svc = AuthService(uow)
        user = _make_user(uow, username="noaudit", last_login=datetime.now(timezone.utc))

        alert = auth_svc.evaluate_login_alert(user, "127.0.0.1", "test-agent")

        assert alert is None

    def test_ip_change_takes_priority_over_ua_change(self, uow):
        """When both IP and UA changed, IP change alert is returned (checked first)."""
        auth_svc = AuthService(uow)
        user = _make_user(uow, username="bothchanged", last_login=datetime.now(timezone.utc))
        _make_audit_log(uow, user.id, ip_address="192.168.1.1", user_agent="old-agent")

        alert = auth_svc.evaluate_login_alert(user, "10.0.0.1", "new-agent")

        assert alert == "Login from a new IP address (Previous: 192.168.1.1)."

    def test_audit_log_without_ip_or_ua_returns_none(self, uow):
        """Audit log with missing ip_address and user_agent returns no alert."""
        auth_svc = AuthService(uow)
        user = _make_user(uow, username="incompleteaudit", last_login=datetime.now(timezone.utc))
        _make_audit_log(uow, user.id, ip_address=None, user_agent=None)

        alert = auth_svc.evaluate_login_alert(user, "127.0.0.1", "test-agent")

        assert alert is None