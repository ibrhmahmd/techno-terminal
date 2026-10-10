"""Tests for auth provisioning (provision_login and link_employee_to_new_user)."""

import secrets
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.modules.auth import provision_login
from app.modules.auth.models.auth_models import User
from app.modules.auth.services.auth_service import AuthService
from app.modules.auth.services.provisioning import _create_supabase_user
from app.shared.constants import MIN_PASSWORD_LENGTH
from app.shared.exceptions import ConflictError, NotFoundError, ValidationError

# Generated per run so no password literal is committed.
TEST_PASSWORD = secrets.token_urlsafe(16)


def _unique_username(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class TestProvisionLogin:
    """Tests for the provision_login facade function."""

    def test_provision_login_success(self, uow):
        """Successful provisioning creates user in session, calls Supabase, does not commit."""
        mock_admin = MagicMock()
        mock_admin.auth.admin.create_user.return_value.user.id = "supabase-uid-123"

        username = _unique_username("testuser")

        with patch("app.modules.auth.services.provisioning.get_supabase_admin", return_value=mock_admin):
            user = provision_login(
                uow,
                username=username,
                raw_password=TEST_PASSWORD,
                role="admin",
                employee_id=None,
                is_active=True,
            )

        assert user.username == username
        assert user.role == "admin"
        assert user.supabase_uid == "supabase-uid-123"
        assert user.is_active is True
        assert user.employee_id is None
        mock_admin.auth.admin.create_user.assert_called_once_with(
            {"email": f"{username}@system.local", "password": TEST_PASSWORD, "email_confirm": True}
        )

    def test_provision_login_success_with_employee(self, uow, db_session):
        """Successful provisioning with employee_id links the employee."""
        from app.modules.hr.models import Employee

        emp = Employee(
            email=f"emp_{uuid.uuid4().hex[:8]}@test.com",
            full_name="Test Employee",
            phone=f"1234567{uuid.uuid4().hex[:3]}",
            job_title="Coach",
            national_id=f"NAT{uuid.uuid4().hex[:8]}",
            university="Test University",
            major="Computer Science",
            is_graduate=True,
            employment_type="full_time",
        )
        db_session.add(emp)
        db_session.commit()
        db_session.refresh(emp)

        mock_admin = MagicMock()
        mock_admin.auth.admin.create_user.return_value.user.id = "supabase-uid-456"

        username = _unique_username("empuser")

        with patch("app.modules.auth.services.provisioning.get_supabase_admin", return_value=mock_admin):
            user = provision_login(
                uow,
                username=username,
                raw_password=TEST_PASSWORD,
                role="admin",
                employee_id=emp.id,
                is_active=True,
            )

        assert user.employee_id == emp.id
        mock_admin.auth.admin.create_user.assert_called_once()

    def test_provision_login_db_failure_cleans_up_supabase(self, uow):
        """DB failure after Supabase create deletes the Supabase user and re-raises."""
        mock_admin = MagicMock()
        mock_admin.auth.admin.create_user.return_value.user.id = "supabase-uid-789"

        with patch("app.modules.auth.services.provisioning.get_supabase_admin", return_value=mock_admin):
            with patch("app.modules.auth.repositories.auth_repository.AuthRepository.create_user", side_effect=Exception("DB error")):
                with pytest.raises(Exception, match="DB error"):
                    provision_login(
                        uow,
                        username=_unique_username("failuser"),
                        raw_password=TEST_PASSWORD,
                        role="admin",
                    )

        mock_admin.auth.admin.create_user.assert_called_once()
        mock_admin.auth.admin.delete_user.assert_called_once_with("supabase-uid-789")

    def test_provision_login_duplicate_username(self, uow, db_session):
        """Duplicate username raises ConflictError and does not call Supabase."""
        username = _unique_username("taken")
        existing = User(
            username=username,
            role="admin",
            supabase_uid=f"existing-uid-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(existing)
        db_session.commit()

        mock_admin = MagicMock()

        with patch("app.modules.auth.services.provisioning.get_supabase_admin", return_value=mock_admin):
            with pytest.raises(ConflictError, match=f"Username '{username}' already exists"):
                provision_login(
                    uow,
                    username=username,
                    raw_password=TEST_PASSWORD,
                    role="admin",
                )

        mock_admin.auth.admin.create_user.assert_not_called()

    def test_provision_login_employee_not_found(self, uow):
        """Non-existent employee_id raises NotFoundError."""
        mock_admin = MagicMock()

        with patch("app.modules.auth.services.provisioning.get_supabase_admin", return_value=mock_admin):
            with patch("app.modules.auth.repositories.auth_repository.AuthRepository.employee_exists", return_value=False):
                with pytest.raises(NotFoundError, match="Employee 999 not found"):
                    provision_login(
                        uow,
                        username=_unique_username("newuser"),
                        raw_password=TEST_PASSWORD,
                        role="admin",
                        employee_id=999,
                    )

        mock_admin.auth.admin.create_user.assert_not_called()

    def test_provision_login_employee_already_linked(self, uow, db_session):
        """Employee with existing linked login raises ConflictError."""
        from app.modules.hr.models import Employee

        # First create a user in the committed session
        existing_user = User(
            username=_unique_username("existinglinked"),
            role="admin",
            supabase_uid=f"existing-linked-uid-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(existing_user)
        db_session.commit()
        db_session.refresh(existing_user)

        emp = Employee(
            email=f"linked_{uuid.uuid4().hex[:8]}@test.com",
            full_name="Linked Employee",
            phone=f"1234567{uuid.uuid4().hex[:3]}",
            job_title="Coach",
            national_id=f"NAT{uuid.uuid4().hex[:8]}",
            university="Test University",
            major="Computer Science",
            is_graduate=True,
            employment_type="full_time",
            user_id=existing_user.id,
        )
        db_session.add(emp)
        db_session.commit()
        db_session.refresh(emp)

        # Also add a linked user to the uow session so get_users_by_employee_id finds it
        linked_user = User(
            username=_unique_username("linkeduser"),
            role="admin",
            supabase_uid=f"linked-uid-{uuid.uuid4().hex[:8]}",
            is_active=True,
            employee_id=emp.id,
        )
        uow.session.add(linked_user)
        uow.session.flush()

        mock_admin = MagicMock()
        mock_admin.auth.admin.create_user.return_value.user.id = "supabase-uid-should-not-be-called"

        with patch("app.modules.auth.services.provisioning.get_supabase_admin", return_value=mock_admin):
            with pytest.raises(ConflictError, match="already has a linked login"):
                provision_login(
                    uow,
                    username=_unique_username("newuser"),
                    raw_password=TEST_PASSWORD,
                    role="admin",
                    employee_id=emp.id,
                )

        mock_admin.auth.admin.create_user.assert_not_called()

    def test_provision_login_short_password(self, uow):
        """Password shorter than MIN_PASSWORD_LENGTH raises ValidationError."""
        mock_admin = MagicMock()

        with patch("app.modules.auth.services.provisioning.get_supabase_admin", return_value=mock_admin):
            with pytest.raises(ValidationError, match=f"at least {MIN_PASSWORD_LENGTH} characters"):
                provision_login(
                    uow,
                    username=_unique_username("newuser"),
                    raw_password="short",
                    role="admin",
                )

        mock_admin.auth.admin.create_user.assert_not_called()

    def test_provision_login_invalid_role(self, uow):
        """Invalid role raises ValidationError."""
        mock_admin = MagicMock()

        with patch("app.modules.auth.services.provisioning.get_supabase_admin", return_value=mock_admin):
            with pytest.raises(ValidationError, match="Invalid role"):
                provision_login(
                    uow,
                    username=_unique_username("newuser"),
                    raw_password=TEST_PASSWORD,
                    role="invalid_role",
                )

        mock_admin.auth.admin.create_user.assert_not_called()

    def test_provision_login_supabase_error_raises_conflict(self, uow):
        """Supabase creation error raises ConflictError."""
        mock_admin = MagicMock()
        mock_admin.auth.admin.create_user.side_effect = Exception("Supabase down")

        with patch("app.modules.auth.services.provisioning.get_supabase_admin", return_value=mock_admin):
            with pytest.raises(ConflictError, match="Supabase error"):
                provision_login(
                    uow,
                    username=_unique_username("newuser"),
                    raw_password=TEST_PASSWORD,
                    role="admin",
                )

    def test_provision_login_email_username_uses_email_as_binding(self, uow):
        """Username containing @ uses it directly as email_binding."""
        mock_admin = MagicMock()
        mock_admin.auth.admin.create_user.return_value.user.id = "supabase-uid-email"

        with patch("app.modules.auth.services.provisioning.get_supabase_admin", return_value=mock_admin):
            user = provision_login(
                uow,
                username="user@example.com",
                raw_password=TEST_PASSWORD,
                role="admin",
            )

        mock_admin.auth.admin.create_user.assert_called_once_with(
            {"email": "user@example.com", "password": TEST_PASSWORD, "email_confirm": True}
        )


class TestCreateSupabaseUserHelper:
    """Tests for the shared _create_supabase_user helper."""

    def test_create_supabase_user_success(self):
        """Helper creates Supabase user and returns native_uid."""
        mock_admin = MagicMock()
        mock_admin.auth.admin.create_user.return_value.user.id = "supabase-uid-helper"

        with patch("app.modules.auth.services.provisioning.get_supabase_admin", return_value=mock_admin):
            uid = _create_supabase_user("testuser", TEST_PASSWORD)

        assert uid == "supabase-uid-helper"
        mock_admin.auth.admin.create_user.assert_called_once_with(
            {"email": "testuser@system.local", "password": TEST_PASSWORD, "email_confirm": True}
        )

    def test_create_supabase_user_error_raises_conflict(self):
        """Supabase error raises ConflictError."""
        mock_admin = MagicMock()
        mock_admin.auth.admin.create_user.side_effect = Exception("Supabase error detail")

        with patch("app.modules.auth.services.provisioning.get_supabase_admin", return_value=mock_admin):
            with pytest.raises(ConflictError, match="Supabase error: Supabase error detail"):
                _create_supabase_user("testuser", TEST_PASSWORD)


class TestLinkEmployeeToNewUser:
    """Tests for AuthService.link_employee_to_new_user (thin wrapper)."""

    def test_link_employee_to_new_user_delegates_to_provision_login(self, uow, db_session):
        """link_employee_to_new_user calls provision_login and commits."""
        from app.modules.hr.models import Employee

        emp = Employee(
            email=f"emp2_{uuid.uuid4().hex[:8]}@test.com",
            full_name="Test Employee 2",
            phone=f"1234567{uuid.uuid4().hex[:3]}",
            job_title="Coach",
            national_id=f"NAT{uuid.uuid4().hex[:8]}",
            university="Test University",
            major="Computer Science",
            is_graduate=True,
            employment_type="full_time",
        )
        db_session.add(emp)
        db_session.commit()
        db_session.refresh(emp)

        mock_admin = MagicMock()
        mock_admin.auth.admin.create_user.return_value.user.id = "supabase-uid-wrapper"

        with patch("app.modules.auth.services.provisioning.get_supabase_admin", return_value=mock_admin):
            auth_svc = AuthService(uow)
            user = auth_svc.link_employee_to_new_user(
                employee_id=emp.id,
                username=_unique_username("wrapperuser"),
                raw_password=TEST_PASSWORD,
                role="admin",
            )

        assert user.username.startswith("wrapperuser_")
        assert user.supabase_uid == "supabase-uid-wrapper"
        assert user.employee_id == emp.id

    def test_link_employee_to_new_user_propagates_validation_errors(self, uow):
        """Validation errors from provision_login propagate."""
        auth_svc = AuthService(uow)
        with pytest.raises(ValidationError, match="at least 12 characters"):
            auth_svc.link_employee_to_new_user(
                employee_id=None,
                username=_unique_username("newuser"),
                raw_password="short",
                role="admin",
            )

    def test_link_employee_to_new_user_propagates_conflict_errors(self, uow, db_session):
        """Conflict errors from provision_login propagate."""
        username = _unique_username("taken")
        existing = User(
            username=username,
            role="admin",
            supabase_uid=f"existing-uid-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(existing)
        db_session.commit()

        auth_svc = AuthService(uow)
        with pytest.raises(ConflictError, match=f"Username '{username}' already exists"):
            auth_svc.link_employee_to_new_user(
                employee_id=None,
                username=username,
                raw_password=TEST_PASSWORD,
                role="admin",
            )