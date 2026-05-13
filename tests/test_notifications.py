"""
Tests for the Notifications Module.
Covers all 6 user stories with independent test classes.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import os
from datetime import datetime, date

from tests.utils.notification_mocks import (
    MockNotificationRepository,
    MockEmailDispatcher,
    MockWhatsAppDispatcher,
)


class _MockSession:
    """Minimal mock session that returns None for .get()."""
    def get(self, model, pk):
        return None
    def exec(self, stmt):
        return _MockResult()
    def add(self, obj):
        pass
    def flush(self):
        pass
    def commit(self):
        pass


class _MockResult:
    def all(self):
        return []
    def first(self):
        return None
    def one(self):
        return 0


@pytest.fixture
def mock_email():
    return MockEmailDispatcher()


@pytest.fixture
def mock_repo():
    return MockNotificationRepository(session=_MockSession())


@pytest.fixture
def enrollment_template():
    from tests.utils.notification_mocks import _MockTemplate
    return _MockTemplate(
        id=1, name="enrollment_confirmation", code="ENROLLMENT_CREATED",
        channel="EMAIL", is_active=True, is_standard=True,
        subject="New Enrollment: {{student_name}}",
        body="<p>Student {{student_name}} enrolled in {{group_name}}</p>",
        variables=["student_name", "group_name", "level_number"],
    )


@pytest.fixture
def enrollment_completed_template():
    from tests.utils.notification_mocks import _MockTemplate
    return _MockTemplate(
        id=2, name="enrollment_completed", code="ENROLLMENT_COMPLETED",
        channel="EMAIL", is_active=True, is_standard=True,
        subject="Enrollment Completed: {{student_name}}",
        body="<p>{{student_name}} completed level {{level_number}}</p>",
        variables=["student_name", "level_number", "completion_date"],
    )


@pytest.fixture
def enrollment_dropped_template():
    from tests.utils.notification_mocks import _MockTemplate
    return _MockTemplate(
        id=3, name="enrollment_dropped", code="ENROLLMENT_DROPPED",
        channel="EMAIL", is_active=True, is_standard=True,
        subject="Enrollment Dropped: {{student_name}}",
        body="<p>{{student_name}} dropped: {{reason}}</p>",
        variables=["student_name", "reason"],
    )


@pytest.fixture
def enrollment_transferred_template():
    from tests.utils.notification_mocks import _MockTemplate
    return _MockTemplate(
        id=4, name="enrollment_transferred", code="ENROLLMENT_TRANSFERRED",
        channel="EMAIL", is_active=True, is_standard=True,
        subject="Enrollment Transferred: {{student_name}}",
        body="<p>{{student_name}} moved from {{from_group_name}} to {{to_group_name}}</p>",
        variables=["student_name", "from_group_name", "to_group_name"],
    )


@pytest.fixture
def level_progression_template():
    from tests.utils.notification_mocks import _MockTemplate
    return _MockTemplate(
        id=5, name="level_progression", code="LEVEL_PROGRESSION",
        channel="EMAIL", is_active=True, is_standard=True,
        subject="Level Progression: {{student_name}}",
        body="<p>{{student_name}} advanced to level {{new_level}}</p>",
        variables=["student_name", "old_level", "new_level"],
    )


# ── US1: Enrollment Notifications ───────────────────────────────────────

class TestEnrollmentNotifications:

    @pytest.mark.asyncio
    async def test_enrollment_created_sends_notification(self, mock_repo, mock_email,
                                                          enrollment_template):
        from app.modules.notifications.services.enrollment_notifications import (
            EnrollmentNotificationService
        )
        mock_repo.templates["enrollment_confirmation"] = enrollment_template
        svc = EnrollmentNotificationService(mock_repo)
        svc._email = mock_email
        svc._resolve_notification_recipients = Mock(return_value=[
            ("admin@test.com", 1, "ADDITIONAL")
        ])
        svc._get_group_name = Mock(return_value="Test Group")
        svc._get_instructor_name = Mock(return_value="Test Instructor")
        svc._get_student_name = Mock(return_value="Test Student")

        await svc._process_created(student_id=1, enrollment_id=10, group_id=5, level_number=1)

        assert len(mock_email.sent_emails) == 1
        email = mock_email.sent_emails[0]
        assert email.recipient == "admin@test.com"
        assert "Test Student" in email.body
        assert "Test Group" in email.body

    @pytest.mark.asyncio
    async def test_enrollment_created_skips_when_template_inactive(self, mock_repo, mock_email,
                                                                    enrollment_template):
        from app.modules.notifications.services.enrollment_notifications import (
            EnrollmentNotificationService
        )
        enrollment_template.is_active = False
        mock_repo.templates["enrollment_confirmation"] = enrollment_template
        svc = EnrollmentNotificationService(mock_repo)
        svc._email = mock_email

        await svc._process_created(student_id=1, enrollment_id=10, group_id=5, level_number=1)

        assert len(mock_email.sent_emails) == 0

    @pytest.mark.asyncio
    async def test_enrollment_completed_sends_notification(self, mock_repo, mock_email,
                                                            enrollment_completed_template):
        from app.modules.notifications.services.enrollment_notifications import (
            EnrollmentNotificationService
        )
        mock_repo.templates["enrollment_completed"] = enrollment_completed_template
        svc = EnrollmentNotificationService(mock_repo)
        svc._email = mock_email
        svc._resolve_notification_recipients = Mock(return_value=[
            ("admin@test.com", 1, "ADDITIONAL")
        ])
        svc._get_group_name = Mock(return_value="Test Group")
        svc._get_student_name = Mock(return_value="Test Student")

        await svc._process_completed(
            student_id=1, enrollment_id=10, group_id=5,
            level_number=2, completion_date=datetime(2026, 5, 1),
        )

        assert len(mock_email.sent_emails) == 1
        assert "Test Student" in mock_email.sent_emails[0].body
        assert "2" in mock_email.sent_emails[0].subject or "2" in mock_email.sent_emails[0].body

    @pytest.mark.asyncio
    async def test_enrollment_dropped_sends_notification(self, mock_repo, mock_email,
                                                          enrollment_dropped_template):
        from app.modules.notifications.services.enrollment_notifications import (
            EnrollmentNotificationService
        )
        mock_repo.templates["enrollment_dropped"] = enrollment_dropped_template
        svc = EnrollmentNotificationService(mock_repo)
        svc._email = mock_email
        svc._resolve_notification_recipients = Mock(return_value=[
            ("admin@test.com", 1, "ADDITIONAL")
        ])
        svc._get_student_name = Mock(return_value="Test Student")

        await svc._process_dropped(
            student_id=1, enrollment_id=10, group_id=5,
            reason="Transferred to another center", dropped_by=1,
        )

        assert len(mock_email.sent_emails) == 1
        assert "Transferred to another center" in mock_email.sent_emails[0].body

    @pytest.mark.asyncio
    async def test_enrollment_transferred_sends_notification(self, mock_repo, mock_email,
                                                              enrollment_transferred_template):
        from app.modules.notifications.services.enrollment_notifications import (
            EnrollmentNotificationService
        )
        mock_repo.templates["enrollment_transferred"] = enrollment_transferred_template
        svc = EnrollmentNotificationService(mock_repo)
        svc._email = mock_email
        svc._resolve_notification_recipients = Mock(return_value=[
            ("admin@test.com", 1, "ADDITIONAL")
        ])
        svc._get_student_name = Mock(return_value="Test Student")

        await svc._process_transferred(
            student_id=1, from_enrollment_id=10, to_enrollment_id=11,
            from_group_id=5, to_group_id=6, transferred_by=1,
        )

        assert len(mock_email.sent_emails) == 1
        assert "Test Student" in mock_email.sent_emails[0].body

    @pytest.mark.asyncio
    async def test_level_progression_sends_notification(self, mock_repo, mock_email,
                                                         level_progression_template):
        from app.modules.notifications.services.enrollment_notifications import (
            EnrollmentNotificationService
        )
        mock_repo.templates["level_progression"] = level_progression_template
        svc = EnrollmentNotificationService(mock_repo)
        svc._email = mock_email
        svc._resolve_notification_recipients = Mock(return_value=[
            ("admin@test.com", 1, "ADDITIONAL")
        ])
        svc._get_group_name = Mock(return_value="Test Group")
        svc._get_student_name = Mock(return_value="Test Student")

        await svc._process_progression(
            student_id=1, old_level=1, new_level=2, group_id=5, enrollment_id=10,
        )

        assert len(mock_email.sent_emails) == 1
        assert "Test Student" in mock_email.sent_emails[0].body

    @pytest.mark.asyncio
    async def test_enrollment_notification_respects_recipient_filter(self, mock_repo, mock_email,
                                                                       enrollment_template):
        from app.modules.notifications.services.enrollment_notifications import (
            EnrollmentNotificationService
        )
        mock_repo.templates["enrollment_confirmation"] = enrollment_template
        svc = EnrollmentNotificationService(mock_repo)
        svc._email = mock_email
        svc._resolve_notification_recipients = Mock(return_value=[])
        svc._get_student_name = Mock(return_value="Test Student")
        svc._get_group_name = Mock(return_value="Test Group")
        svc._get_instructor_name = Mock(return_value="Test Instructor")

        await svc._process_created(student_id=1, enrollment_id=10, group_id=5, level_number=1)

        assert len(mock_email.sent_emails) == 0


# ── US7: Daily Business Report ───────────────────────────────────────────

class TestDailyReport:

    @pytest.fixture
    def daily_report_template(self):
        from tests.utils.notification_mocks import _MockTemplate
        return _MockTemplate(
            id=10, name="daily_report", code="DAILY_REPORT",
            channel="EMAIL", is_active=True, is_standard=True,
            subject="Daily Report - {{date}}",
            body="<html><body><p>Report for {{date}}</p>{{payment_details}}</body></html>",
            variables=["date", "total_revenue", "payment_details"],
        )

    @pytest.fixture
    def mock_aggregates(self):
        return {
            "total_revenue": 15000.0,
            "new_enrollments": 3,
            "sessions_held": 8,
            "absent_count": 2,
            "payment_count": 5,
            "payment_methods": {"cash": 3, "card": 2},
            "instructors_list": ["Ahmed", "Sara"],
            "attendance_rate": 0.875,
            "unpaid_count": 4,
            "payment_details": [
                {"student_name": "Omar", "group_name": "Group A", "amount": 3000.0, "payment_type": "cash"},
                {"student_name": "Ali", "group_name": "Group B", "amount": 2500.0, "payment_type": "card"},
            ],
        }

    @pytest.mark.asyncio
    async def test_send_daily_report_sends_email(self, mock_repo, mock_email,
                                                  daily_report_template, mock_aggregates):
        """T009: Verify send_daily_report dispatches email with correct data."""
        from app.modules.notifications.services.report_notifications import (
            ReportNotificationService
        )
        mock_repo.templates["daily_report"] = daily_report_template
        svc = ReportNotificationService(mock_repo)
        svc._email = mock_email
        svc._resolve_notification_recipients = Mock(return_value=[
            ("admin@test.com", 1, "ADDITIONAL")
        ])
        svc._fetch_daily_aggregates = Mock(return_value=mock_aggregates)

        await svc.send_daily_report()

        assert len(mock_email.sent_emails) == 1
        email = mock_email.sent_emails[0]
        assert email.recipient == "admin@test.com"
        assert "Report for" in email.body
        assert "Omar" in email.body  # payment detail rendered

    @pytest.mark.asyncio
    async def test_send_daily_report_with_pdf_attachment(self, mock_repo, mock_email,
                                                          daily_report_template, mock_aggregates):
        """T009 extended: verify PDF attachment is generated."""
        from app.modules.notifications.services.report_notifications import (
            ReportNotificationService
        )
        mock_repo.templates["daily_report"] = daily_report_template
        svc = ReportNotificationService(mock_repo)
        svc._email = mock_email
        svc._resolve_notification_recipients = Mock(return_value=[
            ("admin@test.com", 1, "ADDITIONAL")
        ])
        svc._fetch_daily_aggregates = Mock(return_value=mock_aggregates)

        await svc.send_daily_report()

        assert len(mock_email.sent_emails) == 1
        attachments = mock_email.sent_emails[0].attachments
        assert attachments is not None
        assert len(attachments) == 1
        filename, pdf_bytes, mime_type = attachments[0]
        assert filename.startswith("daily_report_")
        assert filename.endswith(".pdf")
        assert mime_type == "application/pdf"
        assert len(pdf_bytes) > 100  # non-trivial PDF

    def test_pdf_generates_with_empty_payment_details(self, mock_aggregates):
        """T010: PDF handles empty payment details gracefully."""
        from app.modules.notifications.pdf.daily_report_pdf import generate_daily_report_pdf

        empty_aggregates = dict(mock_aggregates)
        empty_aggregates["payment_details"] = []
        empty_aggregates["payment_methods"] = {}
        empty_aggregates["instructors_list"] = []

        pdf_bytes = generate_daily_report_pdf(date_str="2026-05-13", aggregates=empty_aggregates)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100

    def test_pdf_generates_with_full_data(self, mock_aggregates):
        """T010: PDF generates with all data present (smoke test)."""
        from app.modules.notifications.pdf.daily_report_pdf import generate_daily_report_pdf

        pdf_bytes = generate_daily_report_pdf(date_str="2026-05-13", aggregates=mock_aggregates)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100

    @pytest.mark.asyncio
    async def test_fetch_daily_aggregates_instructors_query(self, mock_repo, mock_email,
                                                             daily_report_template):
        """T011: _fetch_daily_aggregates SQL query structure - verify it runs
        without error by mocking the DB session inside the method."""
        from app.modules.notifications.services.report_notifications import (
            ReportNotificationService
        )
        mock_repo.templates["daily_report"] = daily_report_template
        svc = ReportNotificationService(mock_repo)
        svc._email = mock_email
        svc._resolve_notification_recipients = Mock(return_value=[
            ("admin@test.com", 1, "ADDITIONAL")
        ])

        with patch("app.db.connection.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.exec.return_value = _MockResult()

            aggregates = svc._fetch_daily_aggregates(datetime(2026, 5, 13).date())

            assert isinstance(aggregates, dict)
            assert "instructors_list" in aggregates


# ── US8: Integration Smoke Tests (requires real DB) ─────────────────────

class TestDailyReportIntegration:

    def test_daily_report_fetch_aggregates_runs(self, db_session):
        """End-to-end: fetch daily aggregates from real DB.
        Verifies SQL column fixes (Bug1-3) return data without errors."""
        from app.modules.notifications.repositories.notification_repository import (
            NotificationRepository
        )
        from app.modules.notifications.services.notification_service import (
            NotificationService
        )
        repo = NotificationRepository(db_session)
        svc = NotificationService(repo)

        today = date.today()
        aggregates = svc.report._fetch_daily_aggregates(today)

        assert isinstance(aggregates, dict)
        assert "instructors_list" in aggregates
        assert "payment_details" in aggregates
        assert "payment_count" in aggregates
        assert "total_revenue" in aggregates
        assert "new_enrollments" in aggregates
        assert "sessions_held" in aggregates
        assert "absent_count" in aggregates
        assert "attendance_rate" in aggregates
        assert "unpaid_count" in aggregates

    def test_daily_report_template_exists_and_active(self, db_session):
        """Verify daily_report template is seeded in DB."""
        from app.modules.notifications.repositories.notification_repository import (
            NotificationRepository
        )
        repo = NotificationRepository(db_session)
        template = repo.get_template_by_name("daily_report")
        assert template is not None
        assert template.is_active
        assert "@media print" in template.body
        assert len(template.variables) >= 11

    def test_pdf_bw_no_colors(self):
        """Verify PDF has no colored backgrounds (Bug4).
        Uses mock data — no DB needed."""
        from app.modules.notifications.pdf.daily_report_pdf import (
            generate_daily_report_pdf
        )
        aggregates = {
            "total_revenue": 15000.0,
            "new_enrollments": 3,
            "sessions_held": 8,
            "absent_count": 2,
            "payment_count": 5,
            "payment_methods": {"cash": 3, "card": 2},
            "instructors_list": ["Ahmed", "Sara"],
            "attendance_rate": 0.875,
            "unpaid_count": 4,
            "payment_details": [
                {"student_name": "Omar", "group_name": "Group A",
                 "amount": 3000.0, "payment_type": "cash"},
            ],
        }
        pdf_bytes = generate_daily_report_pdf("2026-05-13", aggregates)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 500
        # Verify no colored hex codes remain
        for color in (b"#4CAF50", b"#2196F3", b"#FF9800", b"#9C27B0",
                      b"#667eea", b"#E65150", b"#2c3e50"):
            assert color not in pdf_bytes, f"PDF still contains color {color.decode()}"

    @pytest.mark.asyncio
    async def test_send_visual_report_email(self, db_session):
        """Send a real email with real data to the fallback inbox for visual inspection.
        
        Run with: py -m pytest tests/test_notifications.py -k test_send_visual -v -s
        Requires GMAIL_SENDER_ADDRESS and GMAIL_APP_PASSWORD env vars.
        """
        from app.modules.notifications.repositories.notification_repository import (
            NotificationRepository
        )
        from app.modules.notifications.services.notification_service import (
            NotificationService
        )
        from app.modules.notifications.pdf.daily_report_pdf import (
            generate_daily_report_pdf
        )
        from app.modules.notifications.dispatchers.email_dispatcher import (
            GmailEmailDispatcher
        )

        FALLBACK_EMAIL = os.getenv("FALLBACK_EMAIL", "ibrahim.ahmd.net@gmail.com")

        # 1. Fetch real data from DB
        repo = NotificationRepository(db_session)
        svc = NotificationService(repo)
        today = date.today()
        aggregates = svc.report._fetch_daily_aggregates(today)

        # 2. Get template and build variables (mirrors send_daily_report logic)
        template = repo.get_template_by_name("daily_report")
        assert template is not None

        payment_methods_str = ", ".join(
            f"{m}: {c}" for m, c in aggregates["payment_methods"].items()
        ) if aggregates["payment_methods"] else "N/A"
        instructors_str = ", ".join(aggregates["instructors_list"]) if aggregates["instructors_list"] else "N/A"

        payment_details_html = ""
        if aggregates["payment_details"]:
            payment_rows = ""
            for p in aggregates["payment_details"]:
                payment_rows += (
                    f"<tr><td style='padding: 8px; border: 1px solid #000;'>{p['student_name']}</td>"
                    f"<td style='padding: 8px; border: 1px solid #000;'>{p['group_name']}</td>"
                    f"<td style='padding: 8px; border: 1px solid #000; text-align: right;'>{p['amount']:.2f} EGP</td>"
                    f"<td style='padding: 8px; border: 1px solid #000;'>{p['payment_type']}</td></tr>"
                )
            payment_details_html = f"""
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px; border: 1px solid #000;">
                <thead>
                    <tr style="background: #333333; color: white;">
                        <th style="padding: 10px; border: 1px solid #000; text-align: left;">Student</th>
                        <th style="padding: 10px; border: 1px solid #000; text-align: left;">Group</th>
                        <th style="padding: 10px; border: 1px solid #000; text-align: right;">Amount</th>
                        <th style="padding: 10px; border: 1px solid #000; text-align: left;">Type</th>
                    </tr>
                </thead>
                <tbody>
                    {payment_rows}
                </tbody>
            </table>
            """

        variables = {
            "date": today.strftime("%Y-%m-%d"),
            "total_revenue": f"{aggregates['total_revenue']:.2f}",
            "new_enrollments": str(aggregates["new_enrollments"]),
            "sessions_held": str(aggregates["sessions_held"]),
            "absent_count": str(aggregates["absent_count"]),
            "payment_count": str(aggregates["payment_count"]),
            "payment_methods": payment_methods_str,
            "payment_details": payment_details_html,
            "instructors_list": instructors_str,
            "attendance_rate": f"{aggregates['attendance_rate']:.1%}",
            "unpaid_count": str(aggregates["unpaid_count"]),
        }

        # 3. Render the email body
        body = template.body
        for key, val in variables.items():
            body = body.replace(f"{{{{{key}}}}}", str(val))

        # 4. Generate PDF
        pdf_bytes = generate_daily_report_pdf(
            date_str=today.strftime("%Y-%m-%d"),
            aggregates=aggregates,
        )

        # 5. Send email
        dispatcher = GmailEmailDispatcher()
        success, error = await dispatcher.send(
            recipient=FALLBACK_EMAIL,
            body=body,
            subject=f"Visual Test - Daily Report {today.strftime('%Y-%m-%d')}",
            attachments=[(f"daily_report_{today.strftime('%Y-%m-%d')}.pdf", pdf_bytes, "application/pdf")],
        )

        assert success, f"Failed to send visual test email: {error}"
        print(f"\nVisual test email sent to {FALLBACK_EMAIL}")
        print("Check your inbox. Inspect:")
        print("  - HTML: Open in browser, use print preview -> verify @media print styles")
        print("  - PDF: Open PDF attachment -> verify B&W readability (no colored backgrounds)")
