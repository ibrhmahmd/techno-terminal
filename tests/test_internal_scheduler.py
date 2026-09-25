"""Tests for reliable scheduled report delivery through the internal trigger endpoints."""
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import logfire
import pytest
from sqlmodel import delete, select

from app.api.dependencies import get_notification_service
from app.core.config import settings
from app.db.connection import get_session
from app.modules.notifications.interfaces.i_report_delivery_ledger import (
    ReportDeliveryLedgerInterface,
)
from app.modules.notifications.models.notification_log import NotificationLog
from app.modules.notifications.models.notification_template import NotificationTemplate
from app.modules.notifications.repositories.report_delivery_ledger import (
    SqlReportDeliveryLedger,
)
from app.modules.notifications.schemas.report_dto import (
    DailyReportAggregateDTO,
    ReportDeliveryResult,
)
from app.modules.notifications.services.notification_service import NotificationService
from app.modules.notifications.services.report_notifications import (
    PeriodReportAggregateDTO,
    ReportNotificationService,
)
from tests.utils.notification_mocks import (
    InMemoryReportDeliveryLedger,
    MockEmailDispatcher,
    MockNotificationRepository,
    _MockTemplate,
)


DEFAULT_RECIPIENTS = [
    ("first@example.com", 1, "ADDITIONAL"),
    ("second@example.com", 2, "ADDITIONAL"),
]


def _report_template(name: str, template_id: int, is_active: bool = True) -> _MockTemplate:
    return _MockTemplate(
        id=template_id,
        name=name,
        code=name.upper(),
        channel="EMAIL",
        is_active=is_active,
        is_standard=True,
        subject=f"{name} report",
        body="<html><body><p>Report for {{date}}</p></body></html>",
        variables=["date"],
    )


def _report_templates() -> dict[str, _MockTemplate]:
    return {
        "daily_report": _report_template("daily_report", 101),
        "weekly_report": _report_template("weekly_report", 102),
        "monthly_report": _report_template("monthly_report", 103),
    }


def _daily_aggregates(report_date: date) -> DailyReportAggregateDTO:
    return DailyReportAggregateDTO(
        date=report_date.isoformat(),
        total_revenue=0.0,
        new_enrollments=0,
        sessions_held=0,
        absent_count=0,
        present_count=0,
        attendance_rate=0.0,
        payment_count=0,
        payment_methods={},
        payment_details=[],
        instructors_list=[],
    )


def _build_report_service(
    ledger: InMemoryReportDeliveryLedger,
    email: MockEmailDispatcher,
    report_date: date,
    recipients: Optional[list[tuple[str, int, str]]] = None,
    templates: Optional[dict[str, _MockTemplate]] = None,
) -> ReportNotificationService:
    available_templates = _report_templates() if templates is None else templates
    service = ReportNotificationService(
        MockNotificationRepository(),
        ledger=ledger,
    )
    service._email = email
    service._get_template_by_name = Mock(
        side_effect=lambda name: available_templates.get(name)
    )
    service._resolve_notification_recipients = Mock(
        return_value=list(DEFAULT_RECIPIENTS if recipients is None else recipients)
    )
    service._fetch_daily_aggregates = Mock(return_value=_daily_aggregates(report_date))
    service._fetch_weekly_aggregates = Mock(return_value=PeriodReportAggregateDTO())
    service._fetch_monthly_aggregates = Mock(return_value=PeriodReportAggregateDTO())
    return service


class TestReportDeliveryService:
    @pytest.fixture(autouse=True)
    def stub_daily_pdf(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.notifications.pdf.daily_report_pdf.generate_daily_report_pdf",
            Mock(return_value=b"%PDF-1.4 stub"),
        )

    @pytest.fixture
    def ledger(self):
        return InMemoryReportDeliveryLedger()

    @pytest.fixture
    def email(self):
        return MockEmailDispatcher()

    @pytest.mark.anyio
    async def test_first_run_sends_every_recipient_and_delivers(
        self, ledger, email
    ):
        report_date = date(2026, 9, 25)
        service = _build_report_service(ledger, email, report_date)

        assert isinstance(ledger, ReportDeliveryLedgerInterface)
        result = await service.send_daily_report(report_date)

        assert result.outcome == "delivered"
        assert result.sent == 2
        assert result.failed == 0
        assert result.skipped == 0
        assert result.period_start == report_date
        assert [captured.recipient for captured in email.sent_emails] == [
            contact for contact, _, _ in DEFAULT_RECIPIENTS
        ]
        assert all(log.report_period_start == report_date for log in ledger.logs)

    @pytest.mark.anyio
    async def test_same_period_rerun_sends_nothing(self, ledger, email):
        report_date = date(2026, 9, 25)
        service = _build_report_service(ledger, email, report_date)
        await service.send_daily_report(report_date)

        result = await service.send_daily_report(report_date)

        assert result.outcome == "nothing_to_send"
        assert result.sent == 0
        assert result.failed == 0
        assert result.skipped == 2
        assert len(email.sent_emails) == 2

    @pytest.mark.anyio
    async def test_one_recipient_failure_is_partial(self, ledger, email):
        report_date = date(2026, 9, 25)
        service = _build_report_service(ledger, email, report_date)
        email.send = AsyncMock(
            side_effect=[(True, None), (False, "smtp refused second")]
        )

        result = await service.send_daily_report(report_date)

        assert result.outcome == "partial"
        assert result.sent == 1
        assert result.failed == 1
        assert result.skipped == 0
        assert result.errors == ["smtp refused second"]
        assert [log.status for log in ledger.logs] == ["SENT", "FAILED"]

    @pytest.mark.anyio
    async def test_rerun_retries_only_failed_recipient(self, ledger, email):
        report_date = date(2026, 9, 25)
        service = _build_report_service(ledger, email, report_date)
        email.send = AsyncMock(
            side_effect=[(True, None), (False, "smtp refused second")]
        )
        await service.send_daily_report(report_date)
        email.send = AsyncMock(return_value=(True, None))

        result = await service.send_daily_report(report_date)

        assert result.outcome == "delivered"
        assert result.sent == 1
        assert result.failed == 0
        assert result.skipped == 1
        assert email.send.await_count == 1
        assert email.send.await_args.args[0] == "second@example.com"

    @pytest.mark.anyio
    async def test_different_periods_can_backfill(self, ledger, email):
        report_date = date(2026, 9, 25)
        service = _build_report_service(ledger, email, report_date)

        first = await service.send_daily_report(report_date)
        backfill = await service.send_daily_report(report_date - timedelta(days=1))

        assert first.outcome == "delivered"
        assert backfill.outcome == "delivered"
        assert backfill.sent == 2
        assert backfill.skipped == 0
        assert backfill.period_start == report_date - timedelta(days=1)
        assert len(email.sent_emails) == 4

    @pytest.mark.anyio
    async def test_daily_period_is_the_target_date(self, ledger, email):
        report_date = date(2026, 9, 25)
        service = _build_report_service(ledger, email, report_date)

        result = await service.send_daily_report(report_date)

        assert result.period_start == date(2026, 9, 25)

    @pytest.mark.anyio
    async def test_weekly_period_is_the_monday_of_the_week(self, ledger, email):
        report_date = date(2026, 9, 25)
        service = _build_report_service(ledger, email, report_date)

        result = await service.send_weekly_report(report_date)

        assert result.report_type == "weekly_report"
        assert result.period_start == date(2026, 9, 21)

    @pytest.mark.anyio
    async def test_monthly_period_is_the_first_day_of_the_month(self, ledger, email):
        report_date = date(2026, 9, 25)
        service = _build_report_service(ledger, email, report_date)

        result = await service.send_monthly_report(report_date)

        assert result.report_type == "monthly_report"
        assert result.period_start == date(2026, 9, 1)

    @pytest.mark.anyio
    async def test_inactive_template_is_disabled_without_work(self, ledger, email):
        report_date = date(2026, 9, 25)
        templates = _report_templates()
        templates["daily_report"].is_active = False
        service = _build_report_service(
            ledger, email, report_date, templates=templates
        )

        result = await service.send_daily_report(report_date)

        assert result.outcome == "disabled"
        assert result.sent == 0
        assert email.sent_emails == []
        assert ledger.logs == []
        service._fetch_daily_aggregates.assert_not_called()

    @pytest.mark.anyio
    async def test_no_recipients_is_disabled_without_work(self, ledger, email):
        report_date = date(2026, 9, 25)
        service = _build_report_service(ledger, email, report_date, recipients=[])

        result = await service.send_weekly_report(report_date)

        assert result.outcome == "disabled"
        assert result.sent == 0
        assert email.sent_emails == []
        assert ledger.logs == []
        service._fetch_weekly_aggregates.assert_not_called()

    @pytest.mark.anyio
    async def test_missing_template_is_not_configured(self, ledger, email):
        report_date = date(2026, 9, 25)
        service = _build_report_service(
            ledger, email, report_date, templates={}
        )

        result = await service.send_monthly_report(report_date)

        assert result.outcome == "not_configured"
        assert result.sent == 0
        assert email.sent_emails == []
        assert ledger.logs == []
        service._resolve_notification_recipients.assert_not_called()
        service._fetch_monthly_aggregates.assert_not_called()

    @pytest.mark.anyio
    async def test_all_recipient_failures_produce_failed_outcome(self, ledger, email):
        report_date = date(2026, 9, 25)
        service = _build_report_service(ledger, email, report_date)
        email.send = AsyncMock(return_value=(False, "smtp unavailable"))

        result = await service.send_daily_report(report_date)

        assert result.outcome == "failed"
        assert result.sent == 0
        assert result.failed == 2
        assert result.errors == ["smtp unavailable"]

    @pytest.mark.anyio
    async def test_dispatcher_exception_is_counted_as_failure(self, ledger, email):
        report_date = date(2026, 9, 25)
        service = _build_report_service(ledger, email, report_date)
        email.send = AsyncMock(side_effect=RuntimeError("smtp exploded"))

        result = await service.send_daily_report(report_date)

        assert result.outcome == "failed"
        assert result.failed == 2
        assert result.errors == ["smtp exploded"]
        assert all(log.status == "FAILED" for log in ledger.logs)

    @pytest.mark.anyio
    async def test_errors_are_distinct_and_capped_at_five(self, ledger, email):
        report_date = date(2026, 9, 25)
        recipients = [
            (f"recipient{index}@example.com", index, "ADDITIONAL")
            for index in range(1, 8)
        ]
        service = _build_report_service(
            ledger, email, report_date, recipients=recipients
        )
        email.send = AsyncMock(
            side_effect=[(False, f"failure {index}") for index in range(1, 8)]
        )

        result = await service.send_daily_report(report_date)

        assert result.outcome == "failed"
        assert result.failed == 7
        assert result.errors == [f"failure {index}" for index in range(1, 6)]

    @pytest.mark.anyio
    async def test_force_bypasses_ledger_and_uses_manual_dispatch(self, ledger, email):
        report_date = date(2026, 9, 25)
        service = _build_report_service(ledger, email, report_date)
        service._dispatch = AsyncMock(return_value=True)

        result = await service.send_weekly_report(report_date, force=True)

        assert result.outcome == "delivered"
        assert result.sent == 2
        assert ledger.logs == []
        assert email.sent_emails == []
        assert service._dispatch.await_count == 2
        first_dispatch = service._dispatch.await_args_list[0]
        assert first_dispatch.args[1] == "EMAIL"
        assert first_dispatch.args[4] == "first@example.com"
        assert first_dispatch.kwargs["attachments"] is None


class TestInternalSchedulerEndpoints:
    ROUTES = [
        (
            "/api/v1/notifications/internal/reports/daily-report/trigger",
            "send_daily_report",
        ),
        (
            "/api/v1/notifications/internal/reports/weekly-report/trigger",
            "send_weekly_report",
        ),
        (
            "/api/v1/notifications/internal/reports/monthly-report/trigger",
            "send_monthly_report",
        ),
    ]
    SECRET_CASES = [
        ("missing", "configured", {}),
        ("wrong", "configured", {"X-Internal-Trigger-Secret": "wrong-secret"}),
        ("unconfigured", "unconfigured", {"X-Internal-Trigger-Secret": "any-secret"}),
    ]

    @pytest.fixture
    def notification_service_override(self, app):
        service = Mock()
        app.dependency_overrides[get_notification_service] = lambda: service
        try:
            yield service
        finally:
            app.dependency_overrides.pop(get_notification_service, None)

    @pytest.fixture
    def configured_secret(self, monkeypatch):
        monkeypatch.setattr(settings, "internal_trigger_secret", "test-secret-123")

    @pytest.mark.parametrize("route,method_name", ROUTES)
    @pytest.mark.parametrize("case,secret_state,headers", SECRET_CASES)
    def test_secret_guard_rejects_every_invalid_case(
        self,
        client,
        route,
        method_name,
        case,
        secret_state,
        headers,
        monkeypatch,
    ):
        monkeypatch.setattr(
            settings,
            "internal_trigger_secret",
            "" if secret_state == "unconfigured" else "test-secret-123",
        )

        response = client.post(route, headers=headers)

        assert response.status_code == 401
        assert response.json()["success"] is False
        assert response.json()["error"] in ("AuthError", "Unauthorized")

    @pytest.mark.parametrize(
        "outcome,sent,failed,skipped",
        [
            ("delivered", 2, 0, 0),
            ("nothing_to_send", 0, 0, 2),
            ("disabled", 0, 0, 0),
        ],
    )
    def test_success_outcomes_return_200_and_delivery_event(
        self,
        client,
        configured_secret,
        notification_service_override,
        monkeypatch,
        outcome,
        sent,
        failed,
        skipped,
    ):
        report_date = date(2026, 9, 25)
        result = ReportDeliveryResult(
            report_type="daily_report",
            period_start=report_date,
            outcome=outcome,
            sent=sent,
            failed=failed,
            skipped=skipped,
        )
        notification_service_override.send_daily_report = AsyncMock(
            return_value=result
        )
        info_event = Mock()
        error_event = Mock()
        monkeypatch.setattr(logfire, "info", info_event)
        monkeypatch.setattr(logfire, "error", error_event)

        response = client.post(
            self.ROUTES[0][0],
            headers={"X-Internal-Trigger-Secret": "test-secret-123"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"] == result.model_dump(mode="json")
        assert body["message"]
        info_event.assert_called_once_with(
            "scheduled_report_delivered",
            report_type="daily_report",
            period_start="2026-09-25",
            outcome=outcome,
            sent=sent,
            failed=failed,
            skipped=skipped,
        )
        error_event.assert_not_called()

    @pytest.mark.parametrize(
        "outcome,errors",
        [
            ("partial", ["second recipient refused"]),
            ("failed", ["smtp unavailable"]),
            ("not_configured", []),
        ],
    )
    def test_failure_outcomes_return_500_and_failure_event(
        self,
        client,
        configured_secret,
        notification_service_override,
        monkeypatch,
        outcome,
        errors,
    ):
        report_date = date(2026, 9, 25)
        result = ReportDeliveryResult(
            report_type="daily_report",
            period_start=report_date,
            outcome=outcome,
            sent=1 if outcome == "partial" else 0,
            failed=1,
            skipped=0,
            errors=errors,
        )
        notification_service_override.send_daily_report = AsyncMock(
            return_value=result
        )
        info_event = Mock()
        error_event = Mock()
        monkeypatch.setattr(logfire, "info", info_event)
        monkeypatch.setattr(logfire, "error", error_event)

        response = client.post(
            self.ROUTES[0][0],
            headers={"X-Internal-Trigger-Secret": "test-secret-123"},
        )

        assert response.status_code == 500
        body = response.json()
        assert body["success"] is False
        assert body["data"] == result.model_dump(mode="json")
        assert body["error"]
        assert body["message"]
        error_event.assert_called_once_with(
            "scheduled_report_failed",
            report_type="daily_report",
            period_start="2026-09-25",
            outcome=outcome,
            sent=result.sent,
            failed=1,
            skipped=0,
            errors=errors,
        )
        info_event.assert_not_called()

    @pytest.mark.parametrize(
        "route,method_name,report_type,report_date",
        [
            (
                "/api/v1/notifications/internal/reports/daily-report/trigger",
                "send_daily_report",
                "daily_report",
                date(2026, 9, 25),
            ),
            (
                "/api/v1/notifications/internal/reports/weekly-report/trigger",
                "send_weekly_report",
                "weekly_report",
                date(2026, 9, 21),
            ),
            (
                "/api/v1/notifications/internal/reports/monthly-report/trigger",
                "send_monthly_report",
                "monthly_report",
                date(2026, 9, 1),
            ),
        ],
    )
    def test_routes_delegate_with_explicit_date_and_force_false(
        self,
        client,
        configured_secret,
        notification_service_override,
        route,
        method_name,
        report_type,
        report_date,
    ):
        result = ReportDeliveryResult(
            report_type=report_type,
            period_start=report_date,
            outcome="delivered",
            sent=1,
        )
        report_method = AsyncMock(return_value=result)
        setattr(notification_service_override, method_name, report_method)

        response = client.post(
            route,
            params={"target_date": report_date.isoformat()},
            headers={"X-Internal-Trigger-Secret": "test-secret-123"},
        )

        assert response.status_code == 200
        report_method.assert_awaited_once_with(
            target_date=report_date,
            force=False,
        )

    def test_default_target_date_is_yesterday_in_cairo(
        self,
        client,
        configured_secret,
        notification_service_override,
    ):
        from app.api.routers.notifications.internal_scheduler_router import (
            _get_yesterday_cairo,
        )

        report_date = _get_yesterday_cairo()
        notification_service_override.send_daily_report = AsyncMock(
            return_value=ReportDeliveryResult(
                report_type="daily_report",
                period_start=report_date,
                outcome="delivered",
                sent=1,
            )
        )

        response = client.post(
            self.ROUTES[0][0],
            headers={"X-Internal-Trigger-Secret": "test-secret-123"},
        )

        assert response.status_code == 200
        notification_service_override.send_daily_report.assert_awaited_once_with(
            target_date=report_date,
            force=False,
        )


@pytest.fixture
def ledger_case(db_session):
    tag = uuid4().hex
    contact = f"ledger-{tag}@example.com"
    template = NotificationTemplate(
        name=f"ledger_test_{tag}",
        channel="EMAIL",
        subject="Ledger test",
        body="<p>Ledger test</p>",
        variables=[],
        is_standard=False,
        is_active=False,
    )
    db_session.add(template)
    db_session.commit()
    template_id = template.id

    try:
        yield {
            "template_id": template_id,
            "recipient_contact": contact,
            "period_start": date(2026, 9, 25),
        }
    finally:
        with get_session() as session:
            session.exec(
                delete(NotificationLog).where(
                    NotificationLog.recipient_contact == contact
                )
            )
            session.exec(
                delete(NotificationTemplate).where(
                    NotificationTemplate.id == template_id
                )
            )
            session.commit()


def _claim(ledger: SqlReportDeliveryLedger, case: dict, body: str = "Ledger body"):
    return ledger.claim(
        template_id=case["template_id"],
        period_start=case["period_start"],
        recipient_type="ADDITIONAL",
        recipient_id=424242,
        recipient_contact=case["recipient_contact"],
        subject="Ledger test",
        body=body,
    )


class TestSqlReportDeliveryLedger:
    def test_duplicate_claim_returns_none(self, ledger_case):
        ledger = SqlReportDeliveryLedger()

        first = _claim(ledger, ledger_case)
        duplicate = _claim(ledger, ledger_case)

        assert isinstance(first, int)
        assert duplicate is None

    def test_claim_succeeds_after_previous_claim_is_marked_failed(
        self, ledger_case
    ):
        ledger = SqlReportDeliveryLedger()
        first = _claim(ledger, ledger_case)

        assert isinstance(first, int)
        ledger.mark(first, "FAILED", "smtp unavailable")
        retry = _claim(ledger, ledger_case)

        assert isinstance(retry, int)
        assert retry != first

    def test_stale_pending_claim_is_taken_over(self, db_session, ledger_case):
        ledger = SqlReportDeliveryLedger()
        stale = NotificationLog(
            template_id=ledger_case["template_id"],
            channel="EMAIL",
            recipient_type="ADDITIONAL",
            recipient_id=424242,
            recipient_contact=ledger_case["recipient_contact"],
            subject="Ledger test",
            body="Stale body",
            status="PENDING",
            report_period_start=ledger_case["period_start"],
            created_at=datetime.now(timezone.utc) - timedelta(minutes=16),
        )
        db_session.add(stale)
        db_session.commit()
        stale_id = stale.id

        claim_id = _claim(ledger, ledger_case)

        assert isinstance(claim_id, int)
        assert claim_id != stale_id
        with get_session() as session:
            rows = list(
                session.exec(
                    select(NotificationLog).where(
                        NotificationLog.recipient_contact
                        == ledger_case["recipient_contact"]
                    )
                ).all()
            )
        rows_by_id = {row.id: row for row in rows}
        assert rows_by_id[stale_id].status == "FAILED"
        assert rows_by_id[stale_id].error_message == "abandoned claim (stale PENDING)"
        assert rows_by_id[claim_id].status == "PENDING"
        assert rows_by_id[claim_id].report_period_start == ledger_case["period_start"]


class TestNotificationServiceReportFacade:
    @pytest.mark.anyio
    async def test_facade_returns_delivery_result_and_forwards_force(self):
        report_date = date(2026, 9, 25)
        expected = ReportDeliveryResult(
            report_type="weekly_report",
            period_start=report_date - timedelta(days=4),
            outcome="delivered",
            sent=1,
        )
        service = NotificationService(MockNotificationRepository())
        service.report.send_weekly_report = AsyncMock(return_value=expected)

        result = await service.send_weekly_report(report_date, force=True)

        assert result is expected
        service.report.send_weekly_report.assert_awaited_once_with(
            report_date,
            force=True,
        )
