"""
Comprehensive authentication endpoint tests — covers all auth routes.

Auth Router: /api/v1/auth/**
Admin Auth Router: /api/v1/admin/**
"""

from unittest.mock import MagicMock, patch
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from tests.utils.jwt_mocks import generate_expired_token
from app.modules.auth.models.auth_models import User
from app.api.dependencies import get_current_user


@pytest.fixture
def db_user(db_session):
    """Creates a reusable test user in the database."""
    user = db_session.exec(
        select(User).where(User.supabase_uid == "test-auth-full-001")
    ).first()
    if user is None:
        user = User(
            username=f"auth_full_user_{uuid.uuid4().hex[:8]}",
            role="admin",
            supabase_uid="test-auth-full-001",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


class TestAuthMe:
    """Tests for GET /api/v1/auth/me and PATCH /api/v1/auth/me."""

    def test_auth_me_success(self, client, override_auth, mock_admin_headers, db_user):
        response = client.get("/api/v1/auth/me", headers=mock_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "role" in data
        assert data["id"] == db_user.id
        assert data["role"] == "admin"

    def test_auth_me_no_token(self, client):
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    def test_auth_me_invalid_token_format(self, client):
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token-format"}
        )

        assert response.status_code == 401

    def test_auth_me_expired_token(self, client):
        expired_token = generate_expired_token(
            user_id="expired-user",
            role="admin",
            email="expired@test.com"
        )

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401

    @patch("app.api.routers.auth_router.AuthService.update_profile")
    def test_update_profile_success(self, mock_update, client, override_auth, mock_admin_headers, db_user):
        from app.modules.auth.schemas.auth_schemas import UserPublic

        fake_user = User(
            id=db_user.id,
            username="updated_username",
            role=db_user.role,
            supabase_uid=db_user.supabase_uid,
            is_active=True,
        )
        mock_update.return_value = fake_user

        response = client.patch(
            "/api/v1/auth/me",
            headers=mock_admin_headers,
            json={"username": "updated_username"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "updated_username"

    @patch("app.api.routers.auth_router.AuthService.update_profile")
    def test_update_profile_duplicate_username(self, mock_update, client, override_auth, mock_admin_headers):
        from app.shared.exceptions import ConflictError

        mock_update.side_effect = ConflictError("Username 'taken' already exists.")

        response = client.patch(
            "/api/v1/auth/me",
            headers=mock_admin_headers,
            json={"username": "taken"}
        )

        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False

    def test_update_profile_unauthorized(self, client):
        response = client.patch(
            "/api/v1/auth/me",
            json={"username": "new_username"}
        )

        assert response.status_code == 401


class TestAuthSessions:
    """Tests for session and activity endpoints."""

    def test_list_sessions_success(self, client, override_auth, mock_admin_headers):
        response = client.get("/api/v1/auth/me/sessions", headers=mock_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_list_activity_success(self, client, override_auth, mock_admin_headers):
        response = client.get("/api/v1/auth/me/activity", headers=mock_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert "total" in data

    @patch("app.api.routers.auth_router.AuthService.logout_all_sessions")
    def test_logout_all_sessions(self, mock_logout, client, override_auth, mock_admin_headers):
        mock_logout.return_value = None

        response = client.post(
            "/api/v1/auth/me/sessions/logout-all",
            headers=mock_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_logout.assert_called_once()

    def test_sessions_unauthorized(self, client):
        response = client.get("/api/v1/auth/me/sessions")
        assert response.status_code == 401

    def test_activity_unauthorized(self, client):
        response = client.get("/api/v1/auth/me/activity")
        assert response.status_code == 401


class TestAuthMFA:
    """Tests for MFA endpoints (stubs)."""

    def test_mfa_status_success(self, client, override_auth, mock_admin_headers):
        response = client.get("/api/v1/auth/me/mfa/status", headers=mock_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["enrolled"] is False

    def test_mfa_enroll_success(self, client, override_auth, mock_admin_headers):
        response = client.post("/api/v1/auth/me/mfa/enroll", headers=mock_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "MFA enrollment is coming soon" in data["message"]

    def test_mfa_status_unauthorized(self, client):
        response = client.get("/api/v1/auth/me/mfa/status")
        assert response.status_code == 401

    def test_mfa_enroll_unauthorized(self, client):
        response = client.post("/api/v1/auth/me/mfa/enroll")
        assert response.status_code == 401


class TestAdminUserManagement:
    """Tests for /api/v1/admin/users endpoints."""

    @patch("app.api.routers.admin_auth_router.AuthService.list_users")
    def test_admin_list_users_success(self, mock_list, client, override_system_admin_auth, system_admin_headers):
        from app.modules.auth.schemas.auth_schemas import UserListResult

        fake_user = User(id=1, username="admin1", role="system_admin", supabase_uid="uid-1", is_active=True)
        mock_list.return_value = UserListResult(items=[fake_user], total=1)

        response = client.get("/api/v1/admin/users", headers=system_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["total"] == 1

    def test_admin_list_users_unauthorized(self, client):
        response = client.get("/api/v1/admin/users")
        assert response.status_code == 401

    @patch("app.api.routers.admin_auth_router.AuthService.get_user")
    def test_admin_get_user_success(self, mock_get, client, override_system_admin_auth, system_admin_headers):
        fake_user = User(id=1, username="target_user", role="admin", supabase_uid="uid-1", is_active=True)
        mock_get.return_value = fake_user

        response = client.get("/api/v1/admin/users/1", headers=system_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "target_user"

    @patch("app.api.routers.admin_auth_router.AuthService.get_user")
    def test_admin_get_user_not_found(self, mock_get, client, override_system_admin_auth, system_admin_headers):
        from app.shared.exceptions import NotFoundError

        mock_get.side_effect = NotFoundError("User 999 not found.")

        response = client.get("/api/v1/admin/users/999", headers=system_admin_headers)

        assert response.status_code == 404

    @patch("app.api.routers.admin_auth_router.AuthService.update_user")
    def test_admin_update_user_success(self, mock_update, client, override_system_admin_auth, system_admin_headers):
        fake_user = User(id=2, username="user2", role="admin", supabase_uid="uid-2", is_active=True)
        mock_update.return_value = fake_user

        response = client.patch(
            "/api/v1/admin/users/2",
            headers=system_admin_headers,
            json={"role": "admin"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("app.api.routers.admin_auth_router.AuthService.delete_user")
    def test_admin_delete_user_success(self, mock_delete, client, override_system_admin_auth, system_admin_headers):
        mock_delete.return_value = None

        response = client.delete(
            "/api/v1/admin/users/3",
            headers=system_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_delete.assert_called_once_with(3, mock_delete.call_args[0][1])

    def test_admin_list_users_with_filters(self, client, override_auth, mock_admin_headers):
        response = client.get(
            "/api/v1/admin/users?role=admin&is_active=true",
            headers=mock_admin_headers
        )

        assert response.status_code == 200

    def test_admin_get_user_unauthorized(self, client):
        response = client.get("/api/v1/admin/users/1")
        assert response.status_code == 401

    def test_admin_update_user_unauthorized(self, client):
        response = client.patch("/api/v1/admin/users/1", json={"role": "admin"})
        assert response.status_code == 401

    def test_admin_delete_user_unauthorized(self, client):
        response = client.delete("/api/v1/admin/users/1")
        assert response.status_code == 401


class TestAdminAudit:
    """Tests for /api/v1/admin/audit endpoints."""

    @patch("app.api.routers.admin_auth_router.AuditService.query_logins")
    def test_admin_audit_logins(self, mock_query, client, override_system_admin_auth, system_admin_headers):
        from app.modules.auth.schemas.auth_schemas import AuditLogQueryResult, AuditLogEntryDTO
        from datetime import datetime

        mock_query.return_value = AuditLogQueryResult(
            items=[], total=0
        )

        response = client.get("/api/v1/admin/audit/logins", headers=system_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert data["total"] == 0

    @patch("app.api.routers.admin_auth_router.AuditService.query_password_changes")
    def test_admin_audit_password_changes(self, mock_query, client, override_system_admin_auth, system_admin_headers):
        from app.modules.auth.schemas.auth_schemas import AuditLogQueryResult

        mock_query.return_value = AuditLogQueryResult(items=[], total=0)

        response = client.get(
            "/api/v1/admin/audit/password-changes",
            headers=system_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    @patch("app.api.routers.admin_auth_router.AuditService.query_failed_attempts")
    def test_admin_audit_failed_attempts(self, mock_query, client, override_system_admin_auth, system_admin_headers):
        from app.modules.auth.schemas.auth_schemas import AuditLogQueryResult

        mock_query.return_value = AuditLogQueryResult(items=[], total=0)

        response = client.get(
            "/api/v1/admin/audit/failed-attempts?from=2024-01-01T00:00:00",
            headers=system_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_admin_audit_logins_unauthorized(self, client):
        response = client.get("/api/v1/admin/audit/logins")
        assert response.status_code == 401

    def test_admin_audit_password_changes_unauthorized(self, client):
        response = client.get("/api/v1/admin/audit/password-changes")
        assert response.status_code == 401

    def test_admin_audit_failed_attempts_unauthorized(self, client):
        response = client.get("/api/v1/admin/audit/failed-attempts?from=2024-01-01T00:00:00")
        assert response.status_code == 401


class TestAuthLoginFlow:
    """Tests for login, register, and forgot-password flows."""

    @patch("app.api.routers.auth_router.AuditService.log_event")
    @patch("app.api.routers.auth_router.get_supabase_anon")
    def test_login_with_invalid_credentials(self, mock_get_anon, mock_audit, client):
        mock_supabase = MagicMock()
        mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")
        mock_get_anon.return_value = mock_supabase

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "bad@test.com", "password": "wrong"}
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    @patch("app.api.routers.auth_router.AuthService.register_with_invite")
    def test_register_without_invite(self, mock_register, client):
        from app.shared.exceptions import AuthError

        mock_register.side_effect = AuthError("Invalid or expired invite token.")

        response = client.post(
            "/api/v1/auth/register",
            json={"token": "invalid-token", "username": "new_user", "password": "strongpassword123"}
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    def test_forgot_password_empty_email(self, client):
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": ""}
        )

        assert response.status_code == 422

    @patch("app.api.routers.auth_router.AuditService.log_event")
    @patch("app.api.routers.auth_router.get_supabase_anon")
    def test_login_with_real_credentials_not_available(self, mock_get_anon, mock_audit, client):
        """Login uses real Supabase — test returns 401 when not configured."""
        mock_supabase = MagicMock()
        mock_supabase.auth.sign_in_with_password.side_effect = Exception("Supabase not configured")
        mock_get_anon.return_value = mock_supabase

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "real@test.com", "password": "realpassword123"}
        )

        assert response.status_code == 401

    def test_register_missing_fields(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"token": "tok", "username": "u"}
        )

        assert response.status_code == 422


class TestPasswordManagement:
    """Tests for change-password and force-reset endpoints."""

    def test_change_password_validation(self, client, override_auth, mock_admin_headers):
        response = client.post(
            "/api/v1/auth/change-password",
            headers=mock_admin_headers,
            json={"current_password": "oldpwd1234567", "new_password": "short"}
        )

        assert response.status_code == 422

    def test_change_password_unauthorized(self, client):
        response = client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "oldpwd1234567", "new_password": "newstrongpwd12345"}
        )

        assert response.status_code == 401

    @patch("app.modules.auth.services.auth_service.get_supabase_anon")
    @patch("app.modules.auth.services.auth_service.get_supabase_admin")
    def test_change_password_wrong_current(self, mock_get_admin, mock_get_anon, client, override_auth, mock_admin_headers):
        mock_supabase = MagicMock()
        mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")
        mock_get_anon.return_value = mock_supabase

        response = client.post(
            "/api/v1/auth/change-password",
            headers=mock_admin_headers,
            json={"current_password": "wrongpassword", "new_password": "newstrongpwd12345"}
        )

        assert response.status_code == 401

    @patch("app.modules.auth.services.auth_service.AuditService.log_event")
    @patch("app.modules.auth.services.auth_service.get_supabase_anon")
    @patch("app.modules.auth.services.auth_service.get_supabase_admin")
    def test_change_password_success(self, mock_get_admin, mock_get_anon, mock_audit, client, override_auth, mock_admin_headers):
        mock_supabase = MagicMock()
        mock_get_anon.return_value = mock_supabase
        mock_admin = MagicMock()
        mock_get_admin.return_value = mock_admin

        response = client.post(
            "/api/v1/auth/change-password",
            headers=mock_admin_headers,
            json={"current_password": "oldpwd1234567", "new_password": "newstrongpwd12345"}
        )

        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_supabase.auth.sign_in_with_password.assert_called_once()
        mock_admin.auth.admin.update_user_by_id.assert_called_once()

    def test_force_reset_unauthorized(self, client):
        response = client.post(
            "/api/v1/auth/users/1/reset-password",
            json={"new_password": "newstrongpwd12345"}
        )

        assert response.status_code == 401

    @patch("app.api.routers.auth_router.AuthService.force_reset_password")
    def test_force_reset_success(self, mock_reset, client, override_auth, mock_admin_headers):
        mock_reset.return_value = None

        response = client.post(
            "/api/v1/auth/users/1/reset-password",
            headers=mock_admin_headers,
            json={"new_password": "newstrongpassword12"}
        )

        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_reset.assert_called_once_with(user_id=1, new_password="newstrongpassword12")


class TestAdminInvite:
    """Tests for /api/v1/admin/users/invite endpoint."""

    @patch("app.api.routers.admin_auth_router.AuthService.invite_user")
    def test_admin_invite_user_success(self, mock_invite, client, override_system_admin_auth, system_admin_headers):
        from app.modules.auth.schemas.auth_schemas import InviteResultDTO

        fake_invite = InviteResultDTO(
            id=10,
            username="invited@test.com",
            role="admin",
            is_active=False,
        )
        mock_invite.return_value = fake_invite

        response = client.post(
            "/api/v1/admin/users/invite",
            headers=system_admin_headers,
            json={"email": "invited@test.com", "role": "admin"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "invited@test.com"
        assert data["data"]["is_active"] is False

    def test_admin_invite_user_unauthorized(self, client):
        response = client.post(
            "/api/v1/admin/users/invite",
            json={"email": "invited@test.com", "role": "admin"}
        )

        assert response.status_code == 401

    @patch("app.api.routers.admin_auth_router.AuthService.invite_user")
    def test_admin_invite_duplicate_email(self, mock_invite, client, override_system_admin_auth, system_admin_headers):
        from app.shared.exceptions import ConflictError

        mock_invite.side_effect = ConflictError("User with email 'taken@test.com' already exists.")

        response = client.post(
            "/api/v1/admin/users/invite",
            headers=system_admin_headers,
            json={"email": "taken@test.com", "role": "admin"}
        )

        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False


class TestAuthLogout:
    """Tests for POST /api/v1/auth/logout."""

    @patch("app.api.routers.auth_router.get_supabase_anon")
    def test_logout_success(self, mock_get_anon, client):
        mock_supabase = MagicMock()
        mock_get_anon.return_value = mock_supabase

        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer some-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_supabase.auth.sign_out.assert_called_once()

    def test_logout_no_token(self, client):
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 200

    @patch("app.api.routers.auth_router.get_supabase_anon")
    def test_logout_supabase_error_logged(self, mock_get_anon, client):
        mock_supabase = MagicMock()
        mock_supabase.auth.sign_out.side_effect = Exception("Connection error")
        mock_get_anon.return_value = mock_supabase

        with patch("app.api.routers.auth_router.logger.warning") as mock_log:
            response = client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": "Bearer some-token"}
            )

            assert response.status_code == 200
            mock_log.assert_called_once()


class TestAuthRefresh:
    """Tests for POST /api/v1/auth/refresh."""

    @patch("app.api.routers.auth_router.get_supabase_anon")
    def test_refresh_token_invalid(self, mock_get_anon, client):
        mock_supabase = MagicMock()
        mock_supabase.auth.refresh_session.side_effect = Exception("Invalid refresh token")
        mock_get_anon.return_value = mock_supabase

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "bad-token"}
        )

        assert response.status_code == 401

    @patch("app.api.routers.auth_router.get_supabase_anon")
    def test_refresh_token_missing_local_user(self, mock_get_anon, client):
        class MockSessionObj:
            access_token = "mock-at"
            refresh_token = "mock-rt"

        class MockUserObj:
            id = "orphan-uid"

        mock_resp = MagicMock()
        mock_resp.session = MockSessionObj()
        mock_resp.user = MockUserObj()

        mock_supabase = MagicMock()
        mock_supabase.auth.refresh_session.return_value = mock_resp
        mock_get_anon.return_value = mock_supabase

        with patch("app.api.routers.auth_router.AuthService.get_user_by_supabase_uid", return_value=None):
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "valid-but-orphan-token"}
            )

            assert response.status_code == 401

    @patch("app.api.routers.auth_router.get_supabase_anon")
    def test_refresh_token_success(self, mock_get_anon, client):
        mock_supabase = MagicMock()
        mock_resp = MagicMock()
        mock_resp.session = MagicMock()
        mock_resp.session.access_token = "new-access-token"
        mock_resp.session.refresh_token = "new-refresh-token"
        mock_resp.user = MagicMock()
        mock_resp.user.id = "test-uid-refresh"
        mock_supabase.auth.refresh_session.return_value = mock_resp
        mock_get_anon.return_value = mock_supabase

        fake_user = User(
            id=5,
            username="refresh_user",
            role="admin",
            supabase_uid="test-uid-refresh",
            is_active=True,
        )

        with patch("app.api.routers.auth_router.AuthService.get_user_by_supabase_uid", return_value=fake_user):
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "valid-refresh-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["access_token"] == "new-access-token"
            assert data["data"]["refresh_token"] == "new-refresh-token"


class TestAdminAuditWithData:
    """Tests audit endpoints that query actual repository data."""

    @patch("app.api.routers.admin_auth_router.AuditService.query_logins")
    def test_audit_logins_with_recent_data(self, mock_query, client, override_system_admin_auth, system_admin_headers):
        from app.modules.auth.schemas.auth_schemas import AuditLogQueryResult, AuditLogEntryDTO
        from datetime import datetime

        mock_entry = AuditLogEntryDTO(
            id=1,
            user_id=1,
            event_type="login_success",
            ip_address="127.0.0.1",
            user_agent="test-agent",
            details=None,
            created_at=datetime(2024, 6, 1, 12, 0, 0),
        )
        mock_query.return_value = AuditLogQueryResult(items=[mock_entry], total=1)

        response = client.get(
            "/api/v1/admin/audit/logins?user_id=1&from=2024-01-01T00:00:00",
            headers=system_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["data"]) == 1
        assert data["data"][0]["event_type"] == "login_success"
        assert data["data"][0]["ip_address"] == "127.0.0.1"
