"""Characterization tests for the Notifications HTTP API (ticket #24).

Pins status codes, envelopes and field shapes of the 28 endpoints under
``/api/v1/notifications`` BEFORE the HTTP layer moves into
``app/modules/notifications/api/``:

    logs router:      POST /absence, POST /receipt/{id}, GET /logs, GET /logs/parent/{id},
                      POST|GET /reports/{daily,weekly,monthly}[/data]
    templates router: GET|POST /templates, GET|PUT|DELETE /templates/{id}, POST /templates/{id}/test
    bulk router:      POST /bulk
    admin settings:   /admin/settings/me[...] (8 endpoints)
    internal cron:    POST /internal/reports/{daily,weekly,monthly}-report/trigger

Safety (read this before editing)
---------------------------------
* Nothing here may send real email/SMS/WhatsApp. Every endpoint that would dispatch
  (absence, receipt, bulk, report triggers, template test, internal triggers) is exercised
  against a ``MagicMock`` service installed through the
  service-provider overrides; the tests assert what the ROUTER does with it.
  Endpoints that only read or edit database rows (logs, templates CRUD, admin settings,
  report ``/data``) run against the real service.
* Admin settings are global rows (admin id 1). Tests that touch them restore the previous
  state in a ``finally`` block / delete the recipients they create.
* The internal trigger secret is set per test with ``monkeypatch``.

Pinned quirks (pinned, not endorsed)
------------------------------------
See the tests marked "current behaviour".
"""

import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.modules.notifications.schemas.report_dto import ReportDeliveryResult

BASE = "/api/v1/notifications"


def _short() -> str:
    return uuid.uuid4().hex[:10]


@pytest.fixture
def fake_svc(app):
    """A MagicMock standing in for every notification service the routers depend on:
    nothing can be dispatched through it. Yields the single mock."""
    from app.modules.notifications.api import deps

    svc = MagicMock()
    svc.send_weekly_report = AsyncMock()
    svc.send_monthly_report = AsyncMock()
    svc.send_daily_report = AsyncMock()
    svc._dispatch = AsyncMock()
    svc.get_report_assets = MagicMock(return_value=([], {}, MagicMock()))
    svc.get_daily_report_pdf_base64 = MagicMock(return_value=("2026-01-01", "UERG"))
    svc.test_and_send_template = AsyncMock()
    providers = [
        deps.get_alert_service, deps.get_payment_notification_service,
        deps.get_report_service, deps.get_template_service,
    ]
    for p in providers:
        app.dependency_overrides[p] = lambda: svc
    try:
        yield svc
    finally:
        for p in providers:
            app.dependency_overrides.pop(p, None)


# ── POST /absence, POST /receipt/{id}, POST /bulk (router -> service hand-off) ─


def test_absence_alert_queues_notification(client_with_uow, override_auth, mock_admin_headers, fake_svc):
    r = client_with_uow.post(
        f"{BASE}/absence", headers=mock_admin_headers,
        json={"student_id": 7, "session_name": "Robotics L1", "session_date": "2026-05-01"},
    )

    assert r.status_code == 200
    assert r.json() == {"success": True, "data": "Absence notification queued", "message": None}
    args = fake_svc.notify_absence.call_args.args
    assert args[:3] == (7, "Robotics L1", "2026-05-01")


def test_absence_alert_validation(client_with_uow, override_auth, mock_admin_headers, fake_svc):
    assert client_with_uow.post(f"{BASE}/absence", headers=mock_admin_headers, json={}).status_code == 422
    fake_svc.notify_absence.assert_not_called()


def test_receipt_notification_queues_payment_notice(client_with_uow, override_auth, mock_admin_headers, fake_svc):
    r = client_with_uow.post(
        f"{BASE}/receipt/55?student_id=3&amount=100.00&receipt_number=R-1", headers=mock_admin_headers
    )

    assert r.status_code == 200
    assert r.json()["data"] == "Payment receipt notification queued"
    assert fake_svc.notify_payment_received.call_args.args[:4] == (55, 3, "100.00", "R-1")


def test_receipt_notification_requires_query_params(client_with_uow, override_auth, mock_admin_headers, fake_svc):
    assert client_with_uow.post(f"{BASE}/receipt/55", headers=mock_admin_headers).status_code == 422


def test_bulk_send(client_with_uow, override_auth, mock_admin_headers, fake_svc):
    fake_svc.send_bulk.return_value = 3

    r = client_with_uow.post(
        f"{BASE}/bulk", headers=mock_admin_headers,
        json={"parent_ids": [1, 2, 3], "template_name": "announcement", "extra_vars": {"k": "v"}},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["data"] == {"queued_count": 3}
    assert body["message"] == "Queued 3 notifications"
    assert fake_svc.send_bulk.call_args.args[:3] == ([1, 2, 3], "announcement", {"k": "v"})


def test_bulk_send_validation(client_with_uow, override_auth, mock_admin_headers, fake_svc):
    assert client_with_uow.post(f"{BASE}/bulk", headers=mock_admin_headers, json={"parent_ids": []}).status_code == 422


# ── GET /logs, GET /logs/parent/{id} (real service, read-only) ────────────────


def test_get_logs_shape(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.get(f"{BASE}/logs?limit=5", headers=mock_admin_headers)

    assert r.status_code == 200
    body = r.json()
    assert set(body) >= {"success", "data", "total", "skip", "limit"}
    assert body["skip"] == 0 and body["limit"] == 5
    assert isinstance(body["total"], int)
    for log in body["data"]:
        assert set(log) == {
            "id", "template_id", "channel", "recipient_type", "recipient_id", "recipient_contact",
            "subject", "body", "status", "error_message", "sent_at", "created_at",
        }


def test_get_logs_filters_accepted(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.get(
        f"{BASE}/logs?status=SENT&channel=EMAIL&recipient_type=PARENT&sort_by=created_at&sort_order=asc",
        headers=mock_admin_headers,
    )
    assert r.status_code == 200
    assert r.json()["total"] >= 0


def test_get_logs_rejects_unknown_filter_and_sort_values(client_with_uow, override_auth, mock_admin_headers):
    """Unknown enum values are a 422 (#141): sort_by=metadata used to be a 500, the rest were ignored."""
    for query in (
        "sort_by=metadata", "sort_by=nonexistent", "sort_order=sideways",
        "status=bogus", "channel=SMS", "recipient_type=nobody", "limit=0", "offset=-1",
    ):
        r = client_with_uow.get(f"{BASE}/logs?{query}", headers=mock_admin_headers)
        assert r.status_code == 422, query
        assert r.json()["error"] == "ValidationError"

    ok = client_with_uow.get(f"{BASE}/logs?sort_by=recipient_contact&sort_order=asc", headers=mock_admin_headers)
    assert ok.status_code == 200


def test_parent_logs_paging_is_bounded(client_with_uow, override_auth, mock_admin_headers):
    """limit/offset are validated (sweep after #141): a negative limit used to reach SQL as a 500."""
    for query in ("limit=-1", "limit=0", "offset=-1", "limit=1000"):
        r = client_with_uow.get(f"{BASE}/logs/parent/1?{query}", headers=mock_admin_headers)
        assert r.status_code == 422, query


def test_get_logs_date_filters(client_with_uow, override_auth, mock_admin_headers, db_session):
    """Fixed in #99 (was a 500: the dates became NAIVE datetimes, which the timestamptz column
    rejects). start_date/end_date are whole Cairo business days."""
    from datetime import date, datetime, timedelta, timezone

    from app.modules.notifications.models.notification_log import NotificationLog

    token = f"datefilter-{_short()}"
    db_session.add(NotificationLog(
        channel="EMAIL", recipient_type="EMPLOYEE", recipient_id=0, recipient_contact=f"{token}@example.com",
        body=token, status="SENT", created_at=datetime.now(timezone.utc),
    ))
    db_session.commit()
    today = date.today()

    def found(start, end):
        r = client_with_uow.get(
            f"{BASE}/logs?search={token}&start_date={start}&end_date={end}", headers=mock_admin_headers
        )
        assert r.status_code == 200
        return r.json()["total"]

    assert found(today - timedelta(days=1), today + timedelta(days=1)) == 1
    assert found("2020-01-01", "2020-01-02") == 0


def test_get_parent_logs(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.get(f"{BASE}/logs/parent/999999999", headers=mock_admin_headers)

    assert r.status_code == 200
    assert r.json()["data"] == []


# ── Report triggers (router logic; dispatch stubbed) ──────────────────────────


def test_daily_report_trigger_returns_pdf(client_with_uow, override_auth, mock_admin_headers, fake_svc):
    r = client_with_uow.post(f"{BASE}/reports/daily?target_date=2026-01-01", headers=mock_admin_headers)

    assert r.status_code == 200
    assert r.json()["data"] == {"date": "2026-01-01", "pdf_base64": "UERG"}


def test_daily_report_trigger_with_recipients_queues_dispatch(
    client_with_uow, override_auth, mock_admin_headers, fake_svc
):
    r = client_with_uow.post(
        f"{BASE}/reports/daily?target_date=2026-01-01", headers=mock_admin_headers,
        json={"email_recipients": ["a@example.com", "b@example.com"]},
    )

    assert r.status_code == 200
    assert r.json()["data"] == "Daily report queued for 2 recipient(s)"


def test_daily_report_trigger_no_data_is_404(client_with_uow, override_auth, mock_admin_headers, fake_svc):
    from app.shared.exceptions import NotFoundError

    fake_svc.get_daily_report_pdf_base64.side_effect = NotFoundError("No data found for 2026-01-01")

    r = client_with_uow.post(f"{BASE}/reports/daily?target_date=2026-01-01", headers=mock_admin_headers)

    assert r.status_code == 404
    assert r.json()["error"] == "NotFoundError"
    assert r.json()["message"] == "No data found for 2026-01-01"


def test_daily_report_trigger_failure_is_500(app, override_auth, mock_admin_headers, fake_svc):
    """Fixed in #99: a failure building the PDF is a 500, not a 404 'No data found'."""
    fake_svc.get_daily_report_pdf_base64.side_effect = RuntimeError("pdf engine down")

    r = TestClient(app, raise_server_exceptions=False).post(
        f"{BASE}/reports/daily?target_date=2026-01-01", headers=mock_admin_headers
    )

    assert r.status_code == 500


def test_report_triggers_reject_future_dates(client_with_uow, override_auth, mock_admin_headers, fake_svc):
    future = (date.today() + timedelta(days=2)).isoformat()
    for period in ("daily", "weekly", "monthly"):
        r = client_with_uow.post(f"{BASE}/reports/{period}?target_date={future}", headers=mock_admin_headers)
        assert r.status_code == 400, period
        assert r.json()["message"] == "Report date cannot be in the future"
    for period in ("daily", "weekly", "monthly"):
        r = client_with_uow.get(f"{BASE}/reports/{period}/data?target_date={future}", headers=mock_admin_headers)
        assert r.status_code == 400, period


def test_weekly_and_monthly_triggers_force_send(client_with_uow, override_auth, mock_admin_headers, fake_svc):
    w = client_with_uow.post(f"{BASE}/reports/weekly?target_date=2026-01-07", headers=mock_admin_headers)
    m = client_with_uow.post(f"{BASE}/reports/monthly?target_date=2026-01-07", headers=mock_admin_headers)

    assert w.status_code == 200 and w.json()["data"] == "Weekly report email queued successfully."
    assert m.status_code == 200 and m.json()["data"] == "Monthly report email queued successfully."
    assert fake_svc.send_weekly_report.call_args.kwargs == {"target_date": date(2026, 1, 7), "force": True}
    assert fake_svc.send_monthly_report.call_args.kwargs == {"target_date": date(2026, 1, 7), "force": True}


def test_invalid_recipient_email_is_422(client_with_uow, override_auth, mock_admin_headers, fake_svc):
    """Fixed by the #86 handler fix (was a 500: the email validator's ValueError could not be
    JSON-serialised by the 422 handler)."""
    r = client_with_uow.post(
        f"{BASE}/reports/daily", headers=mock_admin_headers, json={"email_recipients": ["not-an-email"]}
    )
    assert r.status_code == 422
    assert r.json()["error"] == "ValidationError"


# ── GET /reports/*/data (real service, read-only) ─────────────────────────────


def test_daily_report_data_without_data_is_404(client_with_uow, override_auth, mock_admin_headers):
    """No activity on the day -> 404 NotFoundError (the only 404 left after #99)."""
    r = client_with_uow.get(f"{BASE}/reports/daily/data?target_date=2001-01-02", headers=mock_admin_headers)
    assert r.status_code == 404
    assert r.json()["error"] == "NotFoundError"
    assert r.json()["message"] == "No data found for 2001-01-02"


@pytest.mark.parametrize("period", ["weekly", "monthly"])
def test_weekly_and_monthly_data_without_data_are_zero_aggregates(client_with_uow, override_auth, mock_admin_headers, period):
    """Unchanged by #99: these endpoints have no "no data" check, so an empty period is a 200
    with zero aggregates."""
    r = client_with_uow.get(f"{BASE}/reports/{period}/data?target_date=2001-01-02", headers=mock_admin_headers)
    assert r.status_code == 200
    assert r.json()["success"] is True and isinstance(r.json()["data"], dict)


@pytest.mark.parametrize("period, method", [
    ("daily", "get_daily_report_data"),
    ("weekly", "_fetch_weekly_aggregates"),
    ("monthly", "_fetch_monthly_aggregates"),
])
def test_report_data_failure_is_500_not_404(app, override_auth, mock_admin_headers, fake_svc, period, method):
    """Fixed in #99 (every internal failure was reported as 404 'No data found'): a real
    failure now surfaces as a 500 (and is logged)."""
    getattr(fake_svc, method).side_effect = RuntimeError("database unreachable")

    r = TestClient(app, raise_server_exceptions=False).get(
        f"{BASE}/reports/{period}/data?target_date=2026-01-05", headers=mock_admin_headers
    )

    assert r.status_code == 500


# ── Templates (real service, rows created/removed by the test) ────────────────


def _new_template(client, headers, **over):
    body = {
        "name": f"char_{_short()}", "channel": "EMAIL", "subject": "Hi", "body": "Hello {{name}}",
        "variables": ["name"],
    }
    body.update(over)
    return client.post(f"{BASE}/templates", headers=headers, json=body)


def test_template_unknown_channel_is_422(client_with_uow, override_auth, mock_admin_headers):
    """An unknown channel is a 422 from the schema (#141; was a 500 CHECK violation)."""
    r = _new_template(client_with_uow, mock_admin_headers, channel="SMS")

    assert r.status_code == 422
    assert r.json()["error"] == "ValidationError"


def test_template_crud_roundtrip(client_with_uow, override_auth, mock_admin_headers):
    created = _new_template(client_with_uow, mock_admin_headers)
    assert created.status_code == 200
    assert created.json()["message"] == "Template created"
    tpl = created.json()["data"]
    assert set(tpl) == {
        "id", "name", "channel", "subject", "body", "variables", "is_standard", "is_active",
        "created_at", "updated_at",
    }
    assert tpl["is_standard"] is False and tpl["is_active"] is True
    tid = tpl["id"]
    try:
        got = client_with_uow.get(f"{BASE}/templates/{tid}", headers=mock_admin_headers)
        assert got.status_code == 200 and got.json()["data"]["id"] == tid

        listed = client_with_uow.get(f"{BASE}/templates", headers=mock_admin_headers)
        assert listed.status_code == 200 and tid in [t["id"] for t in listed.json()["data"]]

        upd = client_with_uow.put(f"{BASE}/templates/{tid}", headers=mock_admin_headers, json={"body": "New body"})
        assert upd.status_code == 200
        assert upd.json()["message"] == "Template updated"
        assert upd.json()["data"]["body"] == "New body"
    finally:
        client_with_uow.delete(f"{BASE}/templates/{tid}", headers=mock_admin_headers)
    gone = client_with_uow.get(f"{BASE}/templates/{tid}", headers=mock_admin_headers)
    assert gone.status_code == 404
    assert gone.json()["message"] == "Template not found"


def test_template_delete_response(client_with_uow, override_auth, mock_admin_headers):
    tid = _new_template(client_with_uow, mock_admin_headers).json()["data"]["id"]

    r = client_with_uow.delete(f"{BASE}/templates/{tid}", headers=mock_admin_headers)

    assert r.status_code == 200
    assert r.json()["data"] == "Template deleted successfully"


def test_template_not_found_cases(client_with_uow, override_auth, mock_admin_headers):
    h = mock_admin_headers
    assert client_with_uow.get(f"{BASE}/templates/999999999", headers=h).status_code == 404
    assert client_with_uow.put(f"{BASE}/templates/999999999", headers=h, json={"body": "x"}).status_code == 404
    assert client_with_uow.delete(f"{BASE}/templates/999999999", headers=h).status_code == 404


def test_template_create_validation(client_with_uow, override_auth, mock_admin_headers):
    assert client_with_uow.post(f"{BASE}/templates", headers=mock_admin_headers, json={"name": "x"}).status_code == 422


def test_standard_template_protections(client_with_uow, override_auth, mock_admin_headers, db_session):
    from app.modules.notifications.models.notification_template import NotificationTemplate

    std = NotificationTemplate(
        name=f"std_{_short()}", channel="EMAIL", subject="s", body="b", variables=[], is_standard=True, is_active=True,
    )
    db_session.add(std)
    db_session.commit()
    db_session.refresh(std)

    rename = client_with_uow.put(f"{BASE}/templates/{std.id}", headers=mock_admin_headers, json={"name": "new"})
    delete = client_with_uow.delete(f"{BASE}/templates/{std.id}", headers=mock_admin_headers)

    assert rename.status_code == 400
    assert rename.json()["message"] == "Cannot edit name, channel, or variables of a standard template"
    assert delete.status_code == 400
    assert delete.json()["message"] == "Standard templates cannot be deleted"
    db_session.delete(std)
    db_session.commit()


def test_template_test_endpoint(client_with_uow, override_auth, mock_admin_headers, fake_svc):
    from app.modules.notifications.schemas.template_dto import TemplateTestResultDTO

    fake_svc.test_and_send_template.return_value = TemplateTestResultDTO(
        template_id=5, template_name="t", rendered_subject="s", rendered_body="b",
        recipients_sent=2, recipients_failed=1, errors=["boom"],
    )

    r = client_with_uow.post(f"{BASE}/templates/5/test", headers=mock_admin_headers)

    assert r.status_code == 200
    assert r.json()["message"] == "Test email sent to 2 recipients, 1 failed"
    assert set(r.json()["data"]) == {
        "template_id", "template_name", "rendered_subject", "rendered_body",
        "recipients_sent", "recipients_failed", "errors",
    }


def test_template_test_unknown_template_is_404(client_with_uow, override_auth, mock_admin_headers, fake_svc):
    fake_svc.test_and_send_template.side_effect = ValueError("Template 9 not found")

    r = client_with_uow.post(f"{BASE}/templates/9/test", headers=mock_admin_headers)

    assert r.status_code == 404
    assert r.json()["message"] == "Template 9 not found"


# ── Admin settings (global rows; restored by the tests) ───────────────────────


def test_get_my_settings(client_with_uow, override_auth, mock_admin_headers):
    r = client_with_uow.get(f"{BASE}/admin/settings/me", headers=mock_admin_headers)

    assert r.status_code == 200
    data = r.json()["data"]
    assert set(data) == {"admin_id", "settings", "additional_recipients"}
    assert data["admin_id"] == 1
    assert data["settings"], "defaults are initialised on first read"
    assert set(data["settings"][0]) == {"notification_type", "is_enabled", "channel", "description"}


def test_toggle_and_read_single_setting(client_with_uow, override_auth, mock_admin_headers):
    h = mock_admin_headers
    base = f"{BASE}/admin/settings/me/types/daily_report"
    client_with_uow.get(f"{BASE}/admin/settings/me", headers=h)  # ensure defaults exist
    before = client_with_uow.get(base, headers=h).json()["data"]["is_enabled"]
    try:
        r = client_with_uow.put(base, headers=h, json={"is_enabled": not before})
        assert r.status_code == 200
        assert r.json()["data"] == {
            "notification_type": "daily_report", "is_enabled": not before, "channel": "EMAIL",
            "description": "Daily business summary report",
        }
        assert client_with_uow.get(base, headers=h).json()["data"]["is_enabled"] is (not before)
    finally:
        client_with_uow.put(base, headers=h, json={"is_enabled": before})


def test_bulk_update_settings(client_with_uow, override_auth, mock_admin_headers):
    h = mock_admin_headers
    client_with_uow.get(f"{BASE}/admin/settings/me", headers=h)
    cur = client_with_uow.get(f"{BASE}/admin/settings/me/types/weekly_report", headers=h).json()["data"]["is_enabled"]
    try:
        r = client_with_uow.put(f"{BASE}/admin/settings/me", headers=h, json={"settings": {"weekly_report": not cur}})
        assert r.status_code == 200
        assert r.json()["data"] == {"weekly_report": not cur}
    finally:
        client_with_uow.put(f"{BASE}/admin/settings/me", headers=h, json={"settings": {"weekly_report": cur}})


def test_unknown_setting_type_is_422(client_with_uow, override_auth, mock_admin_headers):
    """An unknown notification type is rejected on read and on write (#141; GET was 404, PUT stored it)."""
    for method in ("get", "put"):
        r = getattr(client_with_uow, method)(
            f"{BASE}/admin/settings/me/types/not_a_type_{_short()}",
            headers=mock_admin_headers,
            **({"json": {"is_enabled": True}} if method == "put" else {}),
        )
        assert r.status_code == 422, method
        assert r.json()["error"] == "ValidationError"


def test_additional_recipient_lifecycle(client_with_uow, override_auth, mock_admin_headers):
    h = mock_admin_headers
    email = f"char_{_short()}@example.com"

    add = client_with_uow.post(
        f"{BASE}/admin/settings/me/additional-recipients", headers=h,
        json={"email": email, "label": "QA", "notification_types": ["daily_report"]},
    )
    assert add.status_code == 201
    rec = add.json()["data"]
    assert set(rec) == {"id", "email", "label", "notification_types", "is_active"}
    assert rec["email"] == email and rec["is_active"] is True
    rid = rec["id"]
    try:
        listed = client_with_uow.get(f"{BASE}/admin/settings/me/additional-recipients", headers=h)
        assert rid in [x["id"] for x in listed.json()["data"]]

        upd = client_with_uow.put(
            f"{BASE}/admin/settings/me/additional-recipients/{rid}", headers=h,
            json={"label": "QA2", "is_active": False},
        )
        assert upd.status_code == 200
        assert upd.json()["data"]["label"] == "QA2" and upd.json()["data"]["is_active"] is False
    finally:
        dele = client_with_uow.delete(f"{BASE}/admin/settings/me/additional-recipients/{rid}", headers=h)
    assert dele.status_code == 200
    assert dele.json()["data"] == {"message": "Recipient removed successfully"}


def test_additional_recipient_errors(client_with_uow, override_auth, mock_admin_headers):
    h = mock_admin_headers
    p = f"{BASE}/admin/settings/me/additional-recipients"
    assert client_with_uow.post(p, headers=h, json={"email": "nope"}).status_code == 422
    assert client_with_uow.put(f"{p}/999999999", headers=h, json={"label": "x"}).status_code == 404
    assert client_with_uow.delete(f"{p}/999999999", headers=h).status_code == 404


# ── Internal cron triggers ────────────────────────────────────────────────────

SECRET = "char-secret-value"
TRIGGERS = ("daily", "weekly", "monthly")


def _ok_result(period="2026-01-01", outcome="delivered", **over):
    return ReportDeliveryResult(report_type="daily", period_start=date.fromisoformat(period), outcome=outcome, **over)


@pytest.mark.parametrize("name", TRIGGERS)
def test_internal_trigger_rejects_missing_wrong_and_unconfigured_secret(
    client_with_uow, fake_svc, monkeypatch, name
):
    url = f"{BASE}/internal/reports/{name}-report/trigger"
    monkeypatch.setattr(settings, "internal_trigger_secret", SECRET)
    assert client_with_uow.post(url).status_code == 401
    wrong = client_with_uow.post(url, headers={"X-Internal-Trigger-Secret": "wrong"})
    assert wrong.status_code == 401
    assert wrong.json()["message"] == "Invalid internal trigger secret"

    monkeypatch.setattr(settings, "internal_trigger_secret", "")
    empty = client_with_uow.post(url, headers={"X-Internal-Trigger-Secret": ""})
    assert empty.status_code == 401
    assert empty.json()["message"] == "Internal trigger secret not configured"
    getattr(fake_svc, f"send_{name}_report").assert_not_called()


@pytest.mark.parametrize("name", TRIGGERS)
def test_internal_trigger_success_envelope(client_with_uow, fake_svc, monkeypatch, name):
    monkeypatch.setattr(settings, "internal_trigger_secret", SECRET)
    getattr(fake_svc, f"send_{name}_report").return_value = _ok_result(sent=2)

    r = client_with_uow.post(
        f"{BASE}/internal/reports/{name}-report/trigger?target_date=2026-01-01",
        headers={"X-Internal-Trigger-Secret": SECRET},
    )

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"success", "data", "message"}
    assert body["success"] is True
    assert body["message"] == "daily delivered for 2026-01-01 (2 sent, 0 failed, 0 skipped)"
    assert body["data"]["outcome"] == "delivered" and body["data"]["sent"] == 2
    assert getattr(fake_svc, f"send_{name}_report").call_args.kwargs == {
        "target_date": date(2026, 1, 1), "force": False,
    }


def test_internal_trigger_failure_outcomes_are_500(client_with_uow, fake_svc, monkeypatch):
    monkeypatch.setattr(settings, "internal_trigger_secret", SECRET)
    fake_svc.send_daily_report.return_value = _ok_result(outcome="failed", failed=1, errors=["smtp down"])

    r = client_with_uow.post(
        f"{BASE}/internal/reports/daily-report/trigger?target_date=2026-01-01",
        headers={"X-Internal-Trigger-Secret": SECRET},
    )

    assert r.status_code == 500
    body = r.json()
    assert body["success"] is False
    assert body["error"] == "ScheduledReportDeliveryError"
    assert body["message"] == "daily delivery failed for 2026-01-01 (0 sent, 1 failed, 0 skipped)"


def test_internal_trigger_defaults_to_yesterday(client_with_uow, fake_svc, monkeypatch):
    monkeypatch.setattr(settings, "internal_trigger_secret", SECRET)
    fake_svc.send_daily_report.return_value = _ok_result(outcome="nothing_to_send")

    r = client_with_uow.post(
        f"{BASE}/internal/reports/daily-report/trigger", headers={"X-Internal-Trigger-Secret": SECRET}
    )

    assert r.status_code == 200
    passed = fake_svc.send_daily_report.call_args.kwargs["target_date"]
    assert isinstance(passed, date) and passed < date.today() + timedelta(days=1)


# ── Auth ──────────────────────────────────────────────────────────────────────


def test_notification_endpoints_require_auth(client):
    for method, path in [
        ("post", "/absence"), ("post", "/receipt/1?student_id=1&amount=1&receipt_number=r"),
        ("get", "/logs"), ("get", "/logs/parent/1"), ("post", "/reports/daily"), ("get", "/reports/daily/data"),
        ("post", "/reports/weekly"), ("get", "/reports/weekly/data"), ("post", "/reports/monthly"),
        ("get", "/reports/monthly/data"), ("get", "/templates"), ("get", "/templates/1"), ("post", "/templates"),
        ("put", "/templates/1"), ("delete", "/templates/1"), ("post", "/templates/1/test"), ("post", "/bulk"),
        ("get", "/admin/settings/me"), ("put", "/admin/settings/me"),
        ("get", "/admin/settings/me/types/x"), ("put", "/admin/settings/me/types/x"),
        ("get", "/admin/settings/me/additional-recipients"), ("post", "/admin/settings/me/additional-recipients"),
        ("put", "/admin/settings/me/additional-recipients/1"), ("delete", "/admin/settings/me/additional-recipients/1"),
    ]:
        r = getattr(client, method)(BASE + path)
        assert r.status_code == 401, (method, path, r.status_code)
