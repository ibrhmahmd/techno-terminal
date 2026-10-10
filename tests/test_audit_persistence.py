"""
Tests to verify audit rows are actually committed and persisted.
These tests MUST FAIL on the buggy code (audit rows lost due to missing commits).
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import select

from app.modules.auth.models.auth_models import User
from app.modules.auth.models.audit_log import AuditLog, AuditLogEventType
from app.modules.auth.schemas.auth_schemas import UserPublic
from tests.utils.jwt_mocks import generate_mock_supabase_token


class TestAuditPersistence:
    """Verify audit rows are committed and visible after HTTP calls."""

    def _get_audit_logs(self, db_session, event_type=None, user_id=None):
        """Helper to query audit logs directly from DB."""
        stmt = select(AuditLog)
        if event_type:
            stmt = stmt.where(AuditLog.event_type == event_type)
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
        return list(db_session.exec(stmt).all())

    @patch("app.modules.auth.api.auth_router.get_supabase_anon")
    def test_login_creates_login_success_audit(self, mock_get_anon, client, override_auth, mock_admin_headers, db_session):
        """LOGIN_SUCCESS audit row must be committed and visible after successful login."""
        mock_supabase = MagicMock()
        mock_resp = MagicMock()
        mock_resp.session = MagicMock()
        mock_resp.session.access_token = "mock-at"
        mock_resp.session.refresh_token = "mock-rt"
        mock_resp.user = MagicMock()
        mock_resp.user.id = "test-login-uid"
        mock_resp.user.email = "login@test.com"
        mock_supabase.auth.sign_in_with_password.return_value = mock_resp
        mock_get_anon.return_value = mock_supabase

        # Ensure user exists in DB
        user = db_session.exec(select(User).where(User.supabase_uid == "test-login-uid")).first()
        if not user:
            user = User(
                username="login_user",
                role="admin",
                supabase_uid="test-login-uid",
                is_active=True,
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "login@test.com", "password": "password123456"},
            headers=mock_admin_headers,
        )

        assert response.status_code == 200

        # Query audit logs in a FRESH session/connection (simulating separate request)
        # Use the db_session fixture which is a separate session
        logs = self._get_audit_logs(db_session, event_type=AuditLogEventType.LOGIN_SUCCESS, user_id=user.id)
        
        # This assertion should FAIL on buggy code (no commit after log_event)
        assert len(logs) >= 1, "LOGIN_SUCCESS audit row not persisted"
        log = logs[-1]
        assert log.event_type == AuditLogEventType.LOGIN_SUCCESS
        assert log.user_id == user.id
        assert log.ip_address is not None
        assert log.user_agent is not None

    @patch("app.modules.auth.api.auth_router.get_supabase_anon")
    def test_login_invalid_credentials_creates_login_failure_audit(self, mock_get_anon, client, db_session):
        """LOGIN_FAILURE audit row must be committed for invalid credentials."""
        mock_supabase = MagicMock()
        mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")
        mock_get_anon.return_value = mock_supabase

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "bad@test.com", "password": "wrong"},
        )

        assert response.status_code == 401

        logs = self._get_audit_logs(db_session, event_type=AuditLogEventType.LOGIN_FAILURE)
        # Filter for our test email in details
        matching_logs = [l for l in logs if l.details and l.details.get("email") == "bad@test.com"]
        
        # This assertion should FAIL on buggy code (no commit after record_login_failure)
        assert len(matching_logs) >= 1, "LOGIN_FAILURE audit row not persisted for invalid credentials"
        log = matching_logs[-1]
        assert log.event_type == AuditLogEventType.LOGIN_FAILURE
        assert log.details.get("email") == "bad@test.com"
        # Original format for invalid_credentials was just {"email": <email>} - no reason field

    @patch("app.modules.auth.api.auth_router.get_supabase_anon")
    def test_login_no_local_identity_creates_login_failure_audit(self, mock_get_anon, client, db_session):
        """LOGIN_FAILURE audit row must be committed for Supabase user with no local mapping."""
        mock_supabase = MagicMock()
        mock_resp = MagicMock()
        mock_resp.session = MagicMock()
        mock_resp.session.access_token = "mock-at"
        mock_resp.session.refresh_token = "mock-rt"
        mock_resp.user = MagicMock()
        mock_resp.user.id = "orphan-uid-no-local"
        mock_resp.user.email = "orphan@test.com"
        mock_supabase.auth.sign_in_with_password.return_value = mock_resp
        mock_get_anon.return_value = mock_supabase

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "orphan@test.com", "password": "password123456"},
        )

        assert response.status_code == 401

        logs = self._get_audit_logs(db_session, event_type=AuditLogEventType.LOGIN_FAILURE)
        matching_logs = [l for l in logs if l.details and l.details.get("supabase_uid") == "orphan-uid-no-local"]
        
        # This assertion should FAIL on buggy code
        assert len(matching_logs) >= 1, "LOGIN_FAILURE audit row not persisted for no local identity"
        log = matching_logs[-1]
        assert log.event_type == AuditLogEventType.LOGIN_FAILURE
        assert log.details.get("supabase_uid") == "orphan-uid-no-local"
        assert log.details.get("reason") == "no local identity"

    @patch("app.modules.auth.services.auth_service.get_supabase_anon")
    @patch("app.modules.auth.services.auth_service.get_supabase_admin")
    def test_change_password_creates_password_change_audit(self, mock_get_admin, mock_get_anon, client, override_auth, mock_admin_headers, db_session):
        """PASSWORD_CHANGE audit row must be committed after successful password change."""
        mock_supabase = MagicMock()
        mock_get_anon.return_value = mock_supabase
        mock_admin = MagicMock()
        mock_get_admin.return_value = mock_admin

        # Use the user created by override_auth fixture (supabase_uid="test-admin-001")
        user = db_session.exec(select(User).where(User.supabase_uid == "test-admin-001")).first()
        assert user is not None, "override_auth user should exist"

        response = client.post(
            "/api/v1/auth/change-password",
            headers=mock_admin_headers,
            json={"current_password": "oldpwd1234567", "new_password": "newstrongpwd12345"}
        )

        assert response.status_code == 200

        logs = self._get_audit_logs(db_session, event_type=AuditLogEventType.PASSWORD_CHANGE, user_id=user.id)
        
        # This assertion should FAIL on buggy code (no commit after log_event)
        assert len(logs) >= 1, "PASSWORD_CHANGE audit row not persisted"
        log = logs[-1]
        assert log.event_type == AuditLogEventType.PASSWORD_CHANGE
        assert log.user_id == user.id

    def test_admin_update_user_creates_role_changed_audit(self, client, override_system_admin_auth, system_admin_headers, db_session):
        """ROLE_CHANGED audit row must be committed after admin updates user."""
        # Create a target user
        target = User(
            username=f"target_{uuid.uuid4().hex[:8]}",
            role="instructor",
            supabase_uid=f"target-{uuid.uuid4().hex}",
            is_active=True,
        )
        db_session.add(target)
        db_session.commit()
        db_session.refresh(target)

        response = client.patch(
            f"/api/v1/admin/users/{target.id}",
            headers=system_admin_headers,
            json={"role": "admin"}
        )

        assert response.status_code == 200

        logs = self._get_audit_logs(db_session, event_type=AuditLogEventType.ROLE_CHANGED, user_id=target.id)
        
        # This assertion should FAIL on buggy code (log_event after commit, no second commit)
        assert len(logs) >= 1, "ROLE_CHANGED audit row not persisted"
        log = logs[-1]
        assert log.event_type == AuditLogEventType.ROLE_CHANGED
        assert log.user_id == target.id
        assert log.details.get("new_role") == "admin"

    def test_login_suspicious_detection_uses_prior_login_success(self, client, override_auth, mock_admin_headers, db_session):
        """Suspicious login detection (new IP/device) depends on prior LOGIN_SUCCESS rows existing."""
        from app.modules.auth.models.audit_log import AuditLogEventType
        from app.shared.datetime_utils import utc_now

        # Use the user from override_auth fixture
        user = db_session.exec(select(User).where(User.supabase_uid == "test-admin-001")).first()
        assert user is not None
        
        # Update last_login to today so it doesn't trigger "first login of day"
        user.last_login = utc_now()
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Pre-seed a LOGIN_SUCCESS audit log with specific IP
        prior_log = AuditLog(
            user_id=user.id,
            event_type=AuditLogEventType.LOGIN_SUCCESS,
            ip_address="192.168.1.100",
            user_agent="OldBrowser/1.0",
        )
        db_session.add(prior_log)
        db_session.commit()

        # Now login with different IP
        mock_supabase = MagicMock()
        mock_resp = MagicMock()
        mock_resp.session = MagicMock()
        mock_resp.session.access_token = "mock-at"
        mock_resp.session.refresh_token = "mock-rt"
        mock_resp.user = MagicMock()
        mock_resp.user.id = "test-admin-001"
        mock_resp.user.email = "test_admin@test.com"
        mock_supabase.auth.sign_in_with_password.return_value = mock_resp

        with patch("app.modules.auth.api.auth_router.get_supabase_anon", return_value=mock_supabase):
            with patch("app.modules.notifications.services.notification_service.NotificationService.notify_admin_login") as mock_notify:
                response = client.post(
                    "/api/v1/auth/login",
                    json={"email": "test_admin@test.com", "password": "password123456"},
                    headers=mock_admin_headers,
                )

        assert response.status_code == 200
        
        # The alert should have been triggered due to IP change
        # This depends on the LOGIN_SUCCESS row being committed and queryable
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args.kwargs
        assert "new IP address" in call_kwargs["alert_reason"]
        assert "192.168.1.100" in call_kwargs["alert_reason"]