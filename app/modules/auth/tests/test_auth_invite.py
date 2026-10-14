"""Invite -> email -> register works end to end (#148).

The invite token used to be dropped on create (``UserCreate`` lacked the
fields) and nothing delivered it, so invited users could never register.
"""
import uuid
from urllib.parse import parse_qs, urlparse
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import settings
from app.modules.auth.api.deps import get_auth_notifier
from app.modules.auth.tests.fakes import FakeAuthNotifier

PROVISIONING = "app.modules.auth.services.provisioning"
BASE_URL = "https://ui.example.test"


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


def _invite(client, headers, email):
    return client.post(
        "/api/v1/admin/users/invite",
        headers=headers,
        json={"email": email, "role": "admin", "employee_id": None},
    )


def test_invite_emails_a_link_that_registers_the_user(
    client_with_uow, override_system_admin_auth, system_admin_headers, fake_notifier, monkeypatch
):
    monkeypatch.setattr(settings, "frontend_base_url", BASE_URL + "/")
    email = f"{uuid.uuid4().hex[:10]}@test.local"

    r = _invite(client_with_uow, system_admin_headers, email)

    assert r.status_code == 200
    assert r.json()["message"] == f"Invite created. The registration link is being emailed to {email}."
    assert len(fake_notifier.invites) == 1
    sent = fake_notifier.invites[0]
    assert sent["email"] == email
    assert sent["expires_at"] is not None
    url = urlparse(sent["register_url"])
    assert f"{url.scheme}://{url.netloc}{url.path}" == f"{BASE_URL}/register"
    token = parse_qs(url.query)["token"][0]

    admin = MagicMock()
    admin.auth.admin.create_user.return_value.user.id = f"sup-{uuid.uuid4().hex}"
    username = f"inv_{uuid.uuid4().hex[:8]}"
    with patch(f"{PROVISIONING}.get_supabase_admin", return_value=admin):
        reg = client_with_uow.post(
            "/api/v1/auth/register",
            json={"token": token, "username": username, "password": "StrongPassword12"},
        )

    assert reg.status_code == 200
    assert reg.json()["data"]["username"] == username
    assert reg.json()["data"]["is_active"] is True


def test_invite_without_frontend_url_sends_nothing(
    client_with_uow, override_system_admin_auth, system_admin_headers, fake_notifier, monkeypatch
):
    monkeypatch.setattr(settings, "frontend_base_url", "")

    r = _invite(client_with_uow, system_admin_headers, f"{uuid.uuid4().hex[:10]}@test.local")

    assert r.status_code == 200
    assert r.json()["message"] == "Invite created, but no email was sent: FRONTEND_BASE_URL is not configured."
    assert fake_notifier.invites == []


def test_invite_survives_a_notifier_failure(
    client_with_uow, override_system_admin_auth, system_admin_headers, fake_notifier, monkeypatch
):
    monkeypatch.setattr(settings, "frontend_base_url", BASE_URL)
    fake_notifier.should_raise = True

    r = _invite(client_with_uow, system_admin_headers, f"{uuid.uuid4().hex[:10]}@test.local")

    assert r.status_code == 200
    assert r.json()["data"]["is_active"] is False


def _employee(db_session, **overrides):
    from app.testing.db_helpers import create_test_employee
    return create_test_employee(db_session, full_name=f"Invitee {uuid.uuid4().hex[:6]}", **overrides)


def test_invite_refused_for_an_inactive_employee(
    client_with_uow, override_system_admin_auth, system_admin_headers, fake_notifier, db_session
):
    """An inactive or deleted employee cannot be invited (#184)."""
    emp = _employee(db_session, is_active=False)

    r = client_with_uow.post(
        "/api/v1/admin/users/invite",
        headers=system_admin_headers,
        json={"email": f"{uuid.uuid4().hex[:10]}@test.local", "role": "admin", "employee_id": emp.id},
    )

    assert r.status_code == 409
    assert r.json()["error"] == "BusinessRuleError"
    assert fake_notifier.invites == []


def test_invite_is_void_once_the_employee_is_deactivated(
    client_with_uow, override_system_admin_auth, system_admin_headers, fake_notifier, db_session, monkeypatch
):
    """Registering with an invite for an employee deactivated since then fails (#184)."""
    monkeypatch.setattr(settings, "frontend_base_url", BASE_URL)
    emp = _employee(db_session)
    r = client_with_uow.post(
        "/api/v1/admin/users/invite",
        headers=system_admin_headers,
        json={"email": f"{uuid.uuid4().hex[:10]}@test.local", "role": "admin", "employee_id": emp.id},
    )
    assert r.status_code == 200, r.text
    token = parse_qs(urlparse(fake_notifier.invites[0]["register_url"]).query)["token"][0]

    emp.is_active = False
    db_session.add(emp)
    db_session.commit()

    admin = MagicMock()
    with patch(f"{PROVISIONING}.get_supabase_admin", return_value=admin):
        reg = client_with_uow.post(
            "/api/v1/auth/register",
            json={"token": token, "username": f"inv_{uuid.uuid4().hex[:8]}", "password": "StrongPassword12"},
        )

    assert reg.status_code == 401
    admin.auth.admin.create_user.assert_not_called()
