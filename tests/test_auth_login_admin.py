"""Tests for auth login admin functions (set_login_active, update_login_status)."""

import secrets
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.modules.auth import (
    set_login_active,
    update_login_status,
    compensate_provisioned_login,
    provision_login,
)
from app.modules.auth.models.auth_models import User
from app.shared.exceptions import NotFoundError

TEST_PASSWORD = secrets.token_urlsafe(16)


def _unique_username(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class TestSetLoginActive:
    """Tests for set_login_active function."""

    def test_set_login_active_success(self, uow):
        """Successfully sets user active status."""
        user = User(
            username=_unique_username("activeuser"),
            role="admin",
            supabase_uid=f"uid-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        uow.session.add(user)
        uow.session.flush()
        uow.session.refresh(user)

        set_login_active(uow, user.id, False)

        # Verify the change was flushed
        uow.session.expire_all()
        refreshed = uow.session.get(User, user.id)
        assert refreshed.is_active is False

    def test_set_login_active_not_found(self, uow):
        """Raises NotFoundError for non-existent user."""
        with pytest.raises(NotFoundError, match="User 99999 not found"):
            set_login_active(uow, 99999, False)


class TestUpdateLoginStatus:
    """Tests for update_login_status function."""

    def test_update_login_status_success(self, uow):
        """Successfully updates user active status and role."""
        user = User(
            username=_unique_username("statususer"),
            role="admin",
            supabase_uid=f"uid-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        uow.session.add(user)
        uow.session.flush()
        uow.session.refresh(user)

        update_login_status(uow, user.id, is_active=False, role="system_admin")

        uow.session.expire_all()
        refreshed = uow.session.get(User, user.id)
        assert refreshed.is_active is False
        assert refreshed.role == "system_admin"

    def test_update_login_status_not_found(self, uow):
        """Raises NotFoundError for non-existent user."""
        with pytest.raises(NotFoundError, match="User 99999 not found"):
            update_login_status(uow, 99999, True, "admin")


class TestCompensateProvisionedLogin:
    """Tests for compensate_provisioned_login function."""

    def test_compensate_provisioned_login_success(self):
        """Successfully deletes Supabase user."""
        mock_admin = MagicMock()
        compensate_provisioned_login("test-uid-123", supabase_admin=mock_admin)
        mock_admin.auth.admin.delete_user.assert_called_once_with("test-uid-123")

    def test_compensate_provisioned_login_swallows_error(self, caplog):
        """Failure is logged and never raised."""
        mock_admin = MagicMock()
        mock_admin.auth.admin.delete_user.side_effect = Exception("Network error")

        # Should not raise
        compensate_provisioned_login("orphan-uid", supabase_admin=mock_admin)

        mock_admin.auth.admin.delete_user.assert_called_once_with("orphan-uid")
        assert "orphaned auth identity orphan-uid requires manual cleanup" in caplog.text


class TestProvisionLoginExtended:
    """Extended tests for provision_login with new parameters."""

    def test_provision_login_with_injected_client(self, uow):
        """Uses injected supabase_admin client."""
        mock_admin = MagicMock()
        mock_admin.auth.admin.create_user.return_value.user.id = "injected-uid"

        user = provision_login(
            uow,
            username=_unique_username("injected"),
            raw_password=TEST_PASSWORD,
            role="admin",
            supabase_admin=mock_admin,
        )

        assert user.supabase_uid == "injected-uid"
        mock_admin.auth.admin.create_user.assert_called_once()

    def test_provision_login_with_custom_remote_error_mapper(self, uow):
        """Uses custom remote_error_mapper for Supabase errors."""
        mock_admin = MagicMock()
        mock_admin.auth.admin.create_user.side_effect = Exception("Email taken")

        def custom_mapper(exc: Exception) -> Exception:
            return ValueError(f"Custom mapping: {exc}")

        with pytest.raises(ValueError, match="Custom mapping: Email taken"):
            provision_login(
                uow,
                username=_unique_username("mapper"),
                raw_password=TEST_PASSWORD,
                role="admin",
                supabase_admin=mock_admin,
                remote_error_mapper=custom_mapper,
            )

    def test_provision_login_created_at_is_set(self, uow):
        """Verifies created_at is set on user creation."""
        mock_admin = MagicMock()
        mock_admin.auth.admin.create_user.return_value.user.id = "created-at-uid"

        user = provision_login(
            uow,
            username=_unique_username("createdat"),
            raw_password=TEST_PASSWORD,
            role="admin",
            supabase_admin=mock_admin,
        )

        assert user.created_at is not None

    def test_provision_login_db_failure_compensates_with_injected_client(self, uow):
        """DB failure after Supabase create deletes user via injected client."""
        mock_admin = MagicMock()
        mock_admin.auth.admin.create_user.return_value.user.id = "fail-uid"

        with patch(
            "app.modules.auth.repositories.auth_repository.AuthRepository.create_user",
            side_effect=Exception("DB error"),
        ):
            with pytest.raises(Exception, match="DB error"):
                provision_login(
                    uow,
                    username=_unique_username("fail"),
                    raw_password=TEST_PASSWORD,
                    role="admin",
                    supabase_admin=mock_admin,
                )

        mock_admin.auth.admin.create_user.assert_called_once()
        mock_admin.auth.admin.delete_user.assert_called_once_with("fail-uid")