"""Audit-log write resilience regressions.

Guards the exact path that surfaced an RLS violation on the cloud testing
DB: POST /auth/login with credentials that fail local mapping must still
persist a login_failure audit row — and an audit write failure must never
break the auth response itself.
"""
from sqlalchemy import func
from sqlmodel import select

from app.modules.auth.models.audit_log import AuditLog, AuditLogEventType


def _failure_count(db_session) -> int:
    return db_session.exec(
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.event_type == AuditLogEventType.LOGIN_FAILURE)
    ).one()


class TestLoginFailureAuditing:
    def test_bad_credentials_return_401_and_persist_audit_row(
        self, client, db_session
    ):
        """Real chain: invalid Supabase credentials -> 401 + audited attempt."""
        before = _failure_count(db_session)

        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "no-such-user@audit.test", "password": "wrong-pass"},
        )

        assert resp.status_code == 401, resp.text

        db_session.expire_all()
        after = _failure_count(db_session)
        assert after == before + 1, (
            f"expected exactly one new login_failure row ({before} -> {after})"
        )
