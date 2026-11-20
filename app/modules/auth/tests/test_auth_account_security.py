"""Account-security fixes: #250 inactive login/refresh, #251 change-email, #252 role type."""
import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import select

from app.modules.auth.api.deps import get_auth_notifier
from app.modules.auth.models.audit_log import AuditLog
from app.modules.auth.models.auth_models import User
from app.modules.auth.services.auth_service import AuthService
from app.modules.auth.tests.fakes import FakeAuthNotifier

AUTH_ROUTER = "app.modules.auth.api.auth_router"
AUTH_SERVICE = "app.modules.auth.services.auth_service"


def _user(session, **kw) -> User:
    user = User(
        username=kw.pop("username", f"u_{uuid.uuid4().hex[:8]}@test.local"),
        role="admin",
        supabase_uid=kw.pop("supabase_uid", f"sec-{uuid.uuid4().hex}"),
        is_active=kw.pop("is_active", True),
        **kw,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _anon(uid):
    resp = MagicMock()
    resp.session.access_token = "acc"
    resp.session.refresh_token = "ref"
    resp.user.id = uid
    return resp


@pytest.fixture
def fake_notifier(client_with_uow):
    app = client_with_uow.app
    fake = FakeAuthNotifier()
    original = app.dependency_overrides.get(get_auth_notifier)
    app.dependency_overrides[get_auth_notifier] = lambda: fake
    yield fake
    if original is None:
        app.dependency_overrides.pop(get_auth_notifier, None)
    else:
        app.dependency_overrides[get_auth_notifier] = original


def test_inactive_login_is_403_without_success_side_effects(client_with_uow, db_session, fake_notifier):
    user = _user(db_session, is_active=False)
    anon = MagicMock()
    anon.auth.sign_in_with_password.return_value = _anon(user.supabase_uid)

    with patch(f"{AUTH_ROUTER}.get_supabase_anon", return_value=anon):
        r = client_with_uow.post("/api/v1/auth/login", json={"email": "x@y.co", "password": "whatever12"})

    assert r.status_code == 403
    assert r.json()["error"] == "ForbiddenError"
    db_session.expire_all()
    assert db_session.get(User, user.id).last_login is None
    # the failure row has no user_id; no success row may exist for this user
    assert db_session.exec(select(AuditLog).where(AuditLog.user_id == user.id)).all() == []
    assert fake_notifier.calls == []


def test_inactive_refresh_is_403(client_with_uow, db_session):
    user = _user(db_session, is_active=False)
    anon = MagicMock()
    anon.auth.refresh_session.return_value = _anon(user.supabase_uid)

    with patch(f"{AUTH_ROUTER}.get_supabase_anon", return_value=anon):
        r = client_with_uow.post("/api/v1/auth/refresh", json={"refresh_token": "old"})

    assert r.status_code == 403


def test_change_email_then_change_password_uses_new_email(uow):
    user = _user(uow.session)
    new_email = f"new_{uuid.uuid4().hex[:8]}@test.local"
    anon, admin = MagicMock(), MagicMock()
    svc = AuthService(uow)

    with patch(f"{AUTH_SERVICE}.get_supabase_anon", return_value=anon), patch(
        f"{AUTH_SERVICE}.get_supabase_admin", return_value=admin
    ):
        svc.change_email(user, new_email)
        assert user.username == new_email
        svc.change_password(user, "OldPassword123", "NewPassword123")

    anon.auth.sign_in_with_password.assert_called_once_with(
        {"email": new_email, "password": "OldPassword123"}
    )


def test_change_email_to_a_taken_username_conflicts(uow):
    from app.shared.exceptions import ConflictError

    user = _user(uow.session)
    other = _user(uow.session)
    admin = MagicMock()

    with patch(f"{AUTH_SERVICE}.get_supabase_admin", return_value=admin), pytest.raises(ConflictError):
        AuthService(uow).change_email(user, other.username)

    admin.auth.admin.update_user_by_id.assert_not_called()


def test_create_user_rejects_the_retired_instructor_role(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.post(
        "/api/v1/auth/users",
        headers=mock_admin_headers,
        json={"employee_id": None, "username": "x@test.local", "password": "StrongPassword12", "role": "instructor"},
    )

    assert r.status_code == 422
