"""POST /auth/reset-password-confirm completes a reset from the email link (#158).

The UI's /reset-password page posts here with the recovery link's access token;
the route did not exist, so every self-service reset was a 404.
"""
import base64
import json
from unittest.mock import MagicMock, patch

from sqlmodel import select

from app.modules.auth.models.audit_log import AuditLog, AuditLogEventType
from app.modules.auth.services.auth_service import is_recovery_session

AUTH_SERVICE = "app.modules.auth.services.auth_service"


def _jwt(amr_method: str) -> str:
    def part(obj) -> str:
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")

    return ".".join([part({"alg": "HS256"}), part({"sub": "x", "amr": [{"method": amr_method}]}), "sig"])


def _confirm(client, token, password="BrandNewPass123"):
    return client.post(
        "/api/v1/auth/reset-password-confirm",
        headers={"Authorization": f"Bearer {token}"},
        json={"new_password": password},
    )


def test_recovery_session_sets_the_new_password(client_with_uow, override_auth, uow):
    admin = MagicMock()

    with patch(f"{AUTH_SERVICE}.get_supabase_admin", return_value=admin):
        r = _confirm(client_with_uow, _jwt("recovery"))

    assert r.status_code == 200
    assert r.json()["message"] == "Password has been reset."
    admin.auth.admin.update_user_by_id.assert_called_once_with(
        "test-admin-001", {"password": "BrandNewPass123"}
    )
    events = uow.session.exec(
        select(AuditLog).where(AuditLog.event_type == AuditLogEventType.PASSWORD_CHANGE)
    ).all()
    assert any((e.details or {}).get("via") == "recovery_link" for e in events)


def test_a_normal_login_session_cannot_reset_without_the_current_password(client_with_uow, override_auth):
    admin = MagicMock()

    with patch(f"{AUTH_SERVICE}.get_supabase_admin", return_value=admin):
        r = _confirm(client_with_uow, _jwt("password"))

    assert r.status_code == 401
    assert r.json()["error"] == "AuthError"
    admin.auth.admin.update_user_by_id.assert_not_called()


def test_short_password_is_422(client_with_uow, override_auth):
    r = _confirm(client_with_uow, _jwt("recovery"), password="short")

    assert r.status_code == 422


def test_is_recovery_session_rejects_malformed_tokens():
    assert is_recovery_session(_jwt("recovery")) is True
    assert is_recovery_session(_jwt("otp")) is False
    assert is_recovery_session("not-a-jwt") is False
    assert is_recovery_session("a.!!!.c") is False
