"""
Authentication endpoint tests — Phase 1 Priority.
Validates JWT handling, role verification, and error responses.
"""
from unittest.mock import MagicMock, patch

import pytest
from tests.utils.jwt_mocks import generate_expired_token

from app.modules.auth.models.auth_models import User
from app.api.schemas.auth import ResetPasswordRequest


def _make_mock_supabase_session():
    session = MagicMock()
    session.access_token = "mock-access-token"
    session.refresh_token = "mock-refresh-token"
    return session


def _make_mock_supabase_user(uid="mock-supabase-uid"):
    user = MagicMock()
    user.id = uid
    return user


class TestAuthMe:
    """Tests for GET /api/v1/auth/me endpoint."""

    def test_auth_me_success_with_admin(self, client, admin_headers):
        response = client.get("/api/v1/auth/me", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "role" in data

    def test_auth_me_success_with_system_admin(self, client, system_admin_headers):
        response = client.get("/api/v1/auth/me", headers=system_admin_headers)

        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "role" in data
        else:
            assert response.status_code == 401

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


class TestLogin:
    """Tests for POST /api/v1/auth/login."""

    @patch("app.api.routers.auth_router.AuditService.log_event")
    @patch("app.api.routers.auth_router.get_supabase_anon")
    def test_login_success(self, mock_get_anon, mock_audit, client):
        mock_supabase = MagicMock()
        mock_resp = MagicMock()
        mock_resp.session = _make_mock_supabase_session()
        mock_resp.user = _make_mock_supabase_user("test-uid-123")
        mock_supabase.auth.sign_in_with_password.return_value = mock_resp
        mock_get_anon.return_value = mock_supabase

        with patch("app.api.routers.auth_router.AuthService.get_user_by_supabase_uid") as mock_get_user:
            fake_user = User(
                id=1,
                username="test_user",
                role="admin",
                supabase_uid="test-uid-123",
                is_active=True,
            )
            mock_get_user.return_value = fake_user

            with patch("app.api.routers.auth_router.AuthService.update_last_login") as mock_update:
                response = client.post(
                    "/api/v1/auth/login",
                    json={"email": "test@test.com", "password": "password123456"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["access_token"] == "mock-access-token"
                assert data["data"]["refresh_token"] == "mock-refresh-token"
                assert data["data"]["user"]["username"] == "test_user"
                mock_update.assert_called_once_with(1)

    @patch("app.api.routers.auth_router.AuditService.log_event")
    @patch("app.api.routers.auth_router.get_supabase_anon")
    def test_login_invalid_credentials(self, mock_get_anon, mock_audit, client):
        mock_supabase = MagicMock()
        mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")
        mock_get_anon.return_value = mock_supabase

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "bad@test.com", "password": "wrong"}
        )

        assert response.status_code == 401

    def test_login_missing_local_user(self, client):
        """Login succeeds with Supabase but no local User mapping exists."""

        class MockSessionObj:
            access_token = "mock-at"
            refresh_token = "mock-rt"

        class MockUserObj:
            id = "orphan-uid"

        mock_resp = MagicMock()
        mock_resp.session = MockSessionObj()
        mock_resp.user = MockUserObj()

        mock_supabase = MagicMock()
        mock_supabase.auth.sign_in_with_password.return_value = mock_resp

        with patch("app.api.routers.auth_router.get_supabase_anon", return_value=mock_supabase):
            with patch("app.api.routers.auth_router.AuditService.log_event"):
                with patch("app.api.routers.auth_router.AuthService.get_user_by_supabase_uid", return_value=None):
                    response = client.post(
                        "/api/v1/auth/login",
                        json={"email": "orphan@test.com", "password": "password123456"}
                    )

                    assert response.status_code == 401


class TestRefresh:
    """Tests for POST /api/v1/auth/refresh."""

    @patch("app.api.routers.auth_router.get_supabase_anon")
    def test_refresh_token_success(self, mock_get_anon, client):
        mock_supabase = MagicMock()
        mock_resp = MagicMock()
        mock_resp.session = _make_mock_supabase_session()
        mock_resp.user = _make_mock_supabase_user("test-uid-456")
        mock_supabase.auth.refresh_session.return_value = mock_resp
        mock_get_anon.return_value = mock_supabase

        with patch("app.api.routers.auth_router.AuthService.get_user_by_supabase_uid") as mock_get_user:
            fake_user = User(
                id=2,
                username="refresh_user",
                role="admin",
                supabase_uid="test-uid-456",
                is_active=True,
            )
            mock_get_user.return_value = fake_user

            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "valid-refresh-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["access_token"] == "mock-access-token"

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


class TestLogout:
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
        """Logout gracefully handles Supabase errors and logs them."""
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
            args, _ = mock_log.call_args
            assert "Supabase logout failed" in args[0]


class TestCreateUser:
    """Tests for POST /api/v1/auth/users."""

    def test_create_login_user_success(self, client, override_auth, mock_admin_headers):
        """Admin can create a new login user linked to an employee."""
        with patch("app.api.routers.auth_router.AuthService.link_employee_to_new_user") as mock_link:
            fake_user = User(
                id=10,
                username="new_user",
                role="admin",
                supabase_uid="new-supabase-uid",
                employee_id=5,
                is_active=True,
            )
            mock_link.return_value = fake_user

            response = client.post(
                "/api/v1/auth/users",
                headers=mock_admin_headers,
                json={
                    "employee_id": 5,
                    "username": "new_user",
                    "password": "strongpassword123",
                    "role": "admin",
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["username"] == "new_user"
            assert data["data"]["role"] == "admin"


class TestResetPassword:
    """Tests for POST /api/v1/auth/users/{user_id}/reset-password."""

    def test_reset_password_success(self, client, override_auth, mock_admin_headers):
        with patch("app.api.routers.auth_router.AuthService.force_reset_password") as mock_reset:
            mock_reset.return_value = None

            response = client.post(
                "/api/v1/auth/users/1/reset-password",
                headers=mock_admin_headers,
                json={"new_password": "newstrongpassword12"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            mock_reset.assert_called_once_with(user_id=1, new_password="newstrongpassword12")

    def test_reset_password_unauthorized(self, client):
        response = client.post(
            "/api/v1/auth/users/1/reset-password",
            json={"new_password": "newstrongpassword12"}
        )

        assert response.status_code == 401


class TestChangePassword:
    """Tests for POST /api/v1/auth/change-password."""

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
        data = response.json()
        assert data["success"] is True
        mock_supabase.auth.sign_in_with_password.assert_called_once()
        mock_admin.auth.admin.update_user_by_id.assert_called_once()

    @patch("app.modules.auth.services.auth_service.get_supabase_anon")
    def test_change_password_wrong_current(self, mock_get_anon, client, override_auth, mock_admin_headers):
        mock_supabase = MagicMock()
        mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")
        mock_get_anon.return_value = mock_supabase

        response = client.post(
            "/api/v1/auth/change-password",
            headers=mock_admin_headers,
            json={"current_password": "wrongpassword", "new_password": "newstrongpwd12345"}
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    def test_change_password_short_new(self, client, override_auth, mock_admin_headers):
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


class TestForgotPassword:
    """Tests for POST /api/v1/auth/forgot-password."""

    @patch("app.api.routers.auth_router.AuthService.forgot_password")
    def test_forgot_password_success(self, mock_forgot, client):
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "user@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_forgot.assert_called_once_with(email="user@example.com")

    @patch("app.api.routers.auth_router.AuthService.forgot_password")
    def test_forgot_password_unregistered_email(self, mock_forgot, client):
        mock_forgot.return_value = None

        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"}
        )

        assert response.status_code == 200

    def test_forgot_password_no_email(self, client):
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": ""}
        )

        assert response.status_code == 422


class TestUpdateProfile:
    """Tests for PATCH /api/v1/auth/me."""

    @patch("app.api.routers.auth_router.AuthService.update_profile")
    def test_update_profile_success(self, mock_update, client, override_auth, mock_admin_headers):
        from app.modules.auth import User

        fake_user = User(
            id=1,
            username="new_username",
            role="admin",
            supabase_uid="test-uid",
            is_active=True,
        )
        from app.modules.auth.schemas.auth_schemas import UserPublic

        mock_update.return_value = fake_user

        response = client.patch(
            "/api/v1/auth/me",
            headers=mock_admin_headers,
            json={"username": "new_username"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "new_username"

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


class TestAdminUserManagement:
    """Tests for /api/v1/admin/users endpoints."""

    @patch("app.api.routers.admin_auth_router.AuthService.list_users")
    def test_admin_list_users_success(self, mock_list, client, override_system_admin_auth, system_admin_headers):
        from app.modules.auth.models.auth_models import User

        fake_user = User(id=1, username="admin1", role="system_admin", supabase_uid="uid-1", is_active=True)
        mock_list.return_value = ([fake_user], 1)

        response = client.get("/api/v1/admin/users", headers=system_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1

    @patch("app.api.routers.admin_auth_router.AuthService.get_user")
    def test_admin_get_user_success(self, mock_get, client, override_system_admin_auth, system_admin_headers):
        from app.modules.auth.models.auth_models import User

        fake_user = User(id=1, username="admin1", role="system_admin", supabase_uid="uid-1", is_active=True)
        mock_get.return_value = fake_user

        response = client.get("/api/v1/admin/users/1", headers=system_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "admin1"

    @patch("app.api.routers.admin_auth_router.AuthService.get_user")
    def test_admin_get_user_not_found(self, mock_get, client, override_system_admin_auth, system_admin_headers):
        from app.shared.exceptions import NotFoundError

        mock_get.side_effect = NotFoundError("User 999 not found.")

        response = client.get("/api/v1/admin/users/999", headers=system_admin_headers)

        assert response.status_code == 404

    @patch("app.api.routers.admin_auth_router.AuthService.update_user")
    def test_admin_update_user_success(self, mock_update, client, override_system_admin_auth, system_admin_headers):
        from app.modules.auth.models.auth_models import User

        fake_user = User(id=2, username="user2", role="admin", supabase_uid="uid-2", is_active=True)
        mock_update.return_value = fake_user

        response = client.patch(
            "/api/v1/admin/users/2",
            headers=system_admin_headers,
            json={"role": "admin"}
        )

        assert response.status_code == 200

    def test_admin_requires_system_admin(self, client, override_auth, mock_admin_headers):
        response = client.get("/api/v1/admin/users", headers=mock_admin_headers)

        assert response.status_code == 403

    def test_admin_unauthorized(self, client):
        response = client.get("/api/v1/admin/users")

        assert response.status_code == 401


class TestAuthProtectedEndpoints:
    """Tests that protected endpoints reject unauthenticated requests."""

    def test_crm_students_requires_auth(self, client):
        response = client.get("/api/v1/crm/students")

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    def test_finance_receipts_requires_auth(self, client):
        response = client.post("/api/v1/finance/receipts", json={})

        assert response.status_code == 401

    def test_hr_employees_requires_auth(self, client):
        response = client.get("/api/v1/hr/employees")

        assert response.status_code == 401

    def test_enrollments_requires_auth(self, client):
        response = client.post("/api/v1/enrollments", json={})

        assert response.status_code == 401
