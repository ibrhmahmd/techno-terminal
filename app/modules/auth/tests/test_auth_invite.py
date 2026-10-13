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
