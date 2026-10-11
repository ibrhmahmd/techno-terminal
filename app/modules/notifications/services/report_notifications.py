"""
app/modules/notifications/services/report_notifications.py
─────────────────────────────────────────────────────────────
Scheduled report notifications for employees.
"""
from datetime import date, timedelta
from typing import Optional
from decimal import Decimal
import logging
from pydantic import BaseModel, ConfigDict

from app.modules.notifications.services.base_notification_service import BaseNotificationService
from app.modules.notifications.interfaces.i_report_delivery_ledger import (
    ReportDeliveryLedgerInterface,
)
from app.modules.notifications.models.notification_template import NotificationTemplate
from app.modules.notifications.repositories.notification_repository import NotificationRepository
from app.modules.notifications.repositories.report_delivery_ledger import SqlReportDeliveryLedger
from app.modules.notifications.repositories.reports_repository import ReportsRepository
from app.db.uow import unit_of_work
from app.modules.notifications.schemas.report_dto import (
    PeriodReportAggregateDTO,
    DailyReportAggregateDTO,
    PaymentTypeGroup,
    SessionDetailItem,
    InstructorSummaryItem,
    PaymentDetailItem,
    ReportDeliveryResult,
    TopDebtorItem,
    UnpaidAttendeeItem,
)


logger = logging.getLogger(__name__)


class ReportNotificationService(BaseNotificationService):
    """Handles: daily, weekly, monthly business reports."""
    
    def __init__(
        self,
        repo: NotificationRepository,
        ledger: Optional[ReportDeliveryLedgerInterface] = None,
    ):
        super().__init__(repo)
        self._ledger: ReportDeliveryLedgerInterface = (
            ledger if ledger is not None else SqlReportDeliveryLedger()
        )
    
    # ── Scheduled Report Methods ─────────────────────────────────────────
    
    async def send_daily_report(
        self,
        target_date: Optional[date] = None,
        *,
        force: bool = False,
    ) -> ReportDeliveryResult:
        """Daily business summary to all admins."""
        report_date = target_date or date.today()
        template = self._get_template_by_name("daily_report")
        if not template:
            logger.warning("daily_report template not found - report is not configured.")
            return ReportDeliveryResult(
                report_type="daily_report",
                period_start=report_date,
                outcome="not_configured",
            )

        recipients = self._resolve_notification_recipients("daily_report")
        if not template.is_active or not recipients:
            return ReportDeliveryResult(
                report_type="daily_report",
                period_start=report_date,
                outcome="disabled",
            )

        aggregates = self._fetch_daily_aggregates(report_date)
        variables = self._build_variables(aggregates, report_date)

        # Generate PDF attachment
        pdf_bytes = None
        try:
            from app.modules.notifications.pdf.daily_report_pdf import generate_daily_report_pdf
            pdf_bytes = generate_daily_report_pdf(
                date_str=report_date.strftime("%Y-%m-%d"),
                aggregates=aggregates
            )
            logger.info(f"Generated daily report PDF for {report_date}")
        except Exception as e:
            logger.error(f"Failed to generate daily report PDF: {e}")

        attachments = None
        if pdf_bytes:
            filename = f"daily_report_{report_date.strftime('%Y-%m-%d')}.pdf"
            attachments = [(filename, pdf_bytes, "application/pdf")]

        return await self._deliver_report(
            template,
            recipients,
            report_date,
            variables,
            attachments=attachments,
            force=force,
        )
    
    async def send_weekly_report(
        self,
        target_date: Optional[date] = None,
        *,
        force: bool = False,
    ) -> ReportDeliveryResult:
        """Weekly business summary to all admins."""
        report_date = target_date or date.today()
        period_start = report_date - timedelta(days=report_date.weekday())
        template = self._get_template_by_name("weekly_report")
        if not template:
            logger.warning("weekly_report template not found - report is not configured.")
            return ReportDeliveryResult(
                report_type="weekly_report",
                period_start=period_start,
                outcome="not_configured",
            )
        
        # Get notification recipients (fallback handled automatically by base service)
        recipients = self._resolve_notification_recipients("weekly_report")
        if not template.is_active or not recipients:
            return ReportDeliveryResult(
                report_type="weekly_report",
                period_start=period_start,
                outcome="disabled",
            )
        
        week_start = period_start
        completed_week_end = week_start + timedelta(days=6)
        week_end = completed_week_end if completed_week_end < date.today() else report_date
        
        aggregates = self._fetch_weekly_aggregates(week_start, week_end)
        
        variables = {
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d"),
            "total_revenue": f"{aggregates.total_revenue:,.2f}",
            "new_students": aggregates.new_students,
            "attendance_rate": f"{aggregates.attendance_rate:.1f}",
            "new_enrollments": aggregates.new_enrollments,
            "total_sessions": aggregates.total_sessions,
            "debtor_count": aggregates.debtor_count,
            "total_debt": f"{aggregates.total_debt:,.2f}",
            "top_groups": aggregates.top_groups,
            "revenue_by_course": aggregates.revenue_by_course,
            "dropped_enrollments": aggregates.dropped_enrollments,
        }

        return await self._deliver_report(
            template,
            recipients,
            period_start,
            variables,
            force=force,
        )

    async def send_monthly_report(
        self,
        target_date: Optional[date] = None,
        *,
        force: bool = False,
    ) -> ReportDeliveryResult:
        """Monthly business summary to all admins."""
        report_date = target_date or date.today()
        period_start = report_date.replace(day=1)
        template = self._get_template_by_name("monthly_report")
        if not template:
            logger.warning("monthly_report template not found - report is not configured.")
            return ReportDeliveryResult(
                report_type="monthly_report",
                period_start=period_start,
                outcome="not_configured",
            )

        # Get notification recipients (fallback handled automatically by base service)
        recipients = self._resolve_notification_recipients("monthly_report")
        if not template.is_active or not recipients:
            return ReportDeliveryResult(
                report_type="monthly_report",
                period_start=period_start,
                outcome="disabled",
            )

        import calendar
        month_start = period_start
        last_day = calendar.monthrange(month_start.year, month_start.month)[1]
        completed_month_end = date(month_start.year, month_start.month, last_day)
        month_end = completed_month_end if completed_month_end < date.today() else report_date

        aggregates = self._fetch_monthly_aggregates(month_start, month_end)

        variables = {
            "month": report_date.strftime("%B %Y"),
            "total_revenue": f"{aggregates.total_revenue:,.2f}",
            "new_enrollments": aggregates.new_enrollments,
            "active_students": aggregates.active_students,
            "total_sessions": aggregates.total_sessions,
            "attendance_rate": f"{aggregates.attendance_rate:.1f}",
            "new_students": aggregates.new_students,
            "dropped_enrollments": aggregates.dropped_enrollments,
            "debtor_count": aggregates.debtor_count,
            "total_debt": f"{aggregates.total_debt:,.2f}",
            "top_courses": aggregates.top_courses,
            "revenue_breakdown": aggregates.revenue_breakdown,
        }
        
        return await self._deliver_report(
            template,
            recipients,
            period_start,
            variables,
            force=force,
        )

    async def _deliver_report(
        self,
        template: NotificationTemplate,
        recipients: list[tuple[str, int, str]],
        period_start: date,
        variables: dict,
        attachments: Optional[list[tuple[str, bytes, str]]] = None,
        force: bool = False,
    ) -> ReportDeliveryResult:
        report_type = template.name
        body = self._render_template(template, variables)
        subject = None
        if template.subject:
            subject = template.subject
            for key, value in variables.items():
                subject = subject.replace(f"{{{{{key}}}}}", str(value))

        sent = 0
        failed = 0
        skipped = 0
        errors: list[str] = []

        def _record_error(message: str) -> None:
            if message not in errors and len(errors) < 5:
                errors.append(message)

        for contact, recipient_id, recipient_type in recipients:
            if force:
                delivered = await self._dispatch(
                    template,
                    "EMAIL",
                    recipient_type,
                    recipient_id,
                    contact,
                    variables,
                    attachments=attachments,
                )
                if delivered:
                    sent += 1
                else:
                    failed += 1
                    _record_error(f"Delivery failed for {contact}")
                continue

            log_id = self._ledger.claim(
                template_id=template.id,
                period_start=period_start,
                recipient_type=recipient_type,
                recipient_id=recipient_id,
                recipient_contact=contact,
                subject=subject,
                body=body,
            )
            if log_id is None:
                skipped += 1
                continue

            try:
                success, error = await self._email.send(contact, body, subject, attachments)
            except Exception as send_error:
                success, error = False, str(send_error)

            if success:
                self._ledger.mark(log_id, "SENT", None)
                sent += 1
            else:
                error_message = error or f"Delivery failed for {contact}"
                self._ledger.mark(log_id, "FAILED", error_message)
                failed += 1
                _record_error(error_message)

        if sent > 0 and failed > 0:
            outcome = "partial"
        elif sent > 0:
            outcome = "delivered"
        elif failed > 0:
            outcome = "failed"
        else:
            outcome = "nothing_to_send"

        return ReportDeliveryResult(
            report_type=report_type,
            period_start=period_start,
            outcome=outcome,
            sent=sent,
            failed=failed,
            skipped=skipped,
            errors=errors,
        )
    
    # ── Public Helpers for Date-Param Endpoints ─────────────────────────

    def get_daily_report_pdf_base64(self, target_date: date) -> tuple[str, str]:
        """Generate PDF and return (date_str, base64_encoded_pdf)."""
        from base64 import b64encode
        from app.modules.notifications.pdf.daily_report_pdf import generate_daily_report_pdf
        aggregates = self._fetch_daily_aggregates(target_date)
        has_data = self._has_data(aggregates)
        if not has_data:
            from app.shared.exceptions import NotFoundError
            raise NotFoundError(f"No data found for {target_date}")
        pdf_bytes = generate_daily_report_pdf(
            date_str=target_date.isoformat(),
            aggregates=aggregates
        )
        return target_date.isoformat(), b64encode(pdf_bytes).decode()

    def get_report_assets(
        self, target_date: date
    ) -> tuple[list[tuple[str, bytes, str]], dict, object]:
        """Build PDF bytes + variables + template for async dispatch. Raises NotFoundError if no data."""
        from app.modules.notifications.pdf.daily_report_pdf import generate_daily_report_pdf
        aggregates = self._fetch_daily_aggregates(target_date)
        has_data = self._has_data(aggregates)
        if not has_data:
            from app.shared.exceptions import NotFoundError
            raise NotFoundError(f"No data found for {target_date}")

        pdf_bytes = generate_daily_report_pdf(
            date_str=target_date.isoformat(),
            aggregates=aggregates
        )
        filename = f"daily_report_{target_date.isoformat()}.pdf"
        attachments = [(filename, pdf_bytes, "application/pdf")]
        variables = self._build_variables(aggregates, target_date)
        template = self._get_template_by_name("daily_report")
        return attachments, variables, template

    def get_daily_report_data(self, target_date: date) -> DailyReportAggregateDTO:
        """Return aggregate data for a date, raising 404 if empty."""
        aggregates = self._fetch_daily_aggregates(target_date)
        has_data = self._has_data(aggregates)
        if not has_data:
            from app.shared.exceptions import NotFoundError
            raise NotFoundError(f"No data found for {target_date}")
        return aggregates

    def _has_data(self, aggregates: DailyReportAggregateDTO) -> bool:
        return (
            aggregates.sessions_held > 0
            or aggregates.payment_count > 0
            or aggregates.new_enrollments > 0
            or aggregates.present_count > 0
            or bool(aggregates.today_unpaid_attendees)
        )

    def _build_variables(
        self, aggregates: DailyReportAggregateDTO, target_date: date
    ) -> dict:
        """Build the template variables dict (shared between all email dispatch modes).

        Produces Precision Engine tonal HTML — no CSS borders for sectioning,
        background-color shifts instead. Renders correctly in Gmail, Outlook,
        and Apple Mail on both desktop and mobile.
        """
        # ── Scalar helpers ───────────────────────────────────────────────
        def _to_html_list(items: list[str]) -> str:
            if not items:
                return "N/A"
            list_items = "".join([f"<li>{item}</li>" for item in items])
            return f'<ul style="margin: 0; padding-left: 20px;">{list_items}</ul>'

        def _chip(status: str) -> str:
            low = status.lower()
            if low in ("paid", "active", "present", "not_paid"):
                return f'<span class="status-teal">{status}</span>'
            return f'<span class="status-amber">{status}</span>'

        payment_methods_list = [f"{method}: {count}" for method, count in aggregates.payment_methods.items()] if aggregates.payment_methods else []
        payment_methods_str = _to_html_list(payment_methods_list)
        instructors_str = _to_html_list(aggregates.instructors_list or [])
        # ── Row helper ───────────────────────────────────────────────────
        def _row_class(idx: int) -> str:
            return 'row-even' if idx % 2 == 0 else 'row-odd'

        # ── Session-3 Unpaid Students Section (Yesterday) ────────────────
        debtors_section = ""
        if aggregates.today_unpaid_attendees:
            rows = ""
            for i, u in enumerate(aggregates.today_unpaid_attendees):
                rows += (
                    f'<tr class="{_row_class(i)}">'
                    f'<td style="padding: 6px 10px;">{u.student_name}</td>'
                    f'<td style="padding: 6px 10px;">{u.group_name}</td>'
                    f'<td style="padding: 6px 10px; text-align: right;">{u.amount_owed:,.2f} EGP</td>'
                    f'</tr>'
                )
            debtors_section = f"""
            <div class="section-default" style="background: #f8f9ff; padding: 20px 32px;">
                <h3 class="section-title" style="font-family: 'Space Grotesk', Arial, sans-serif; font-size: 15px; font-weight: 600; color: #0b1c30; margin: 0 0 8px 0;">Session 3 Alert — Yesterday</h3>
                <table class="data-table" style="margin-top: 8px; width: 100%; border-collapse: collapse; font-size: 12px;">
                    <tr class="header-row"><td style="padding: 8px 10px; color: #fff; font-weight: 600;">Student</td><td style="padding: 8px 10px; color: #fff; font-weight: 600;">Group</td><td style="padding: 8px 10px; color: #fff; font-weight: 600; text-align: right;">Amount</td></tr>
                    {rows}
                </table>
            </div>"""
        else:
            debtors_section = """
            <div class="section-default" style="background: #f8f9ff; padding: 20px 32px;">
                <h3 class="section-title" style="font-family: 'Space Grotesk', Arial, sans-serif; font-size: 15px; font-weight: 600; color: #0b1c30; margin: 0 0 8px 0;">Session 3 Alert — Yesterday</h3>
                <p class="empty-state" style="color: #9ca3af; font-style: italic; font-size: 13px; text-align: center; padding: 16px; background: #ffffff;">No unpaid students in yesterday's session 3 groups.</p>
            </div>"""

        # ── Cumulative Unpaid Students (3+ Sessions) ────────────────────
        cumulative_debtors_section = ""
        if aggregates.cumulative_unpaid_debtors:
            rows = ""
            for i, u in enumerate(aggregates.cumulative_unpaid_debtors):
                rows += (
                    f'<tr class="{_row_class(i)}">'
                    f'<td style="padding: 6px 10px;">{u.student_name}</td>'
                    f'<td style="padding: 6px 10px;">{u.group_name}</td>'
                    f'<td style="padding: 6px 10px; text-align: right;">{u.amount_owed:,.2f} EGP</td>'
                    f'</tr>'
                )
            cumulative_debtors_section = f"""
            <div class="section-white" style="background: #ffffff; padding: 20px 32px;">
                <h3 class="section-title" style="font-family: 'Space Grotesk', Arial, sans-serif; font-size: 15px; font-weight: 600; color: #9a3412; margin: 0 0 8px 0;">Ongoing Debtors (3+ Sessions Attended)</h3>
                <table class="data-table" style="margin-top: 8px; width: 100%; border-collapse: collapse; font-size: 12px;">
                    <tr class="header-row"><td style="padding: 8px 10px; background-color: #b45309; color: #fff; font-weight: 600;">Student</td><td style="padding: 8px 10px; background-color: #b45309; color: #fff; font-weight: 600;">Group</td><td style="padding: 8px 10px; background-color: #b45309; color: #fff; font-weight: 600; text-align: right;">Amount Owed</td></tr>
                    {rows}
                </table>
            </div>"""
        else:
            cumulative_debtors_section = """
            <div class="section-white" style="background: #ffffff; padding: 20px 32px;">
                <h3 class="section-title" style="font-family: 'Space Grotesk', Arial, sans-serif; font-size: 15px; font-weight: 600; color: #9a3412; margin: 0 0 8px 0;">Ongoing Debtors (3+ Sessions Attended)</h3>
                <p class="empty-state" style="color: #9ca3af; font-style: italic; font-size: 13px; text-align: center; padding: 16px; background: #f8f9ff;">No students with 3+ sessions currently have unpaid balances.</p>
            </div>"""

        # ── Tomorrow Preview Section ──────────────────────────────────────
        tomorrow_preview_section = ""
        if aggregates.tomorrow_preview.has_sessions or aggregates.tomorrow_preview.unpaid_attendees:
            preview = aggregates.tomorrow_preview
            unpaid_rows = ""
            for i, u in enumerate(preview.unpaid_attendees):
                unpaid_rows += (
                    f'<tr class="{_row_class(i)}">'
                    f'<td style="padding: 6px 10px;">{u.student_name}</td>'
                    f'<td style="padding: 6px 10px;">{u.group_name}</td>'
                    f'<td style="padding: 6px 10px; text-align: right;">{u.amount_owed:,.2f} EGP</td>'
                    f'<td style="padding: 6px 10px;">{_chip(u.payment_status)}</td>'
                    f'</tr>'
                )
            unpaid_section = ""
            if unpaid_rows:
                unpaid_section = f"""
                <p style="font-size: 12px; font-weight: 600; color: #9a3412; margin: 10px 0 4px 0;">&nbsp;Unpaid attendees for tomorrow:</p>
                <table class="data-table" style="margin-top: 4px; width: 100%; border-collapse: collapse; font-size: 12px;">
                    <tr class="header-row"><td style="padding: 8px 10px; color: #fff; font-weight: 600;">Student</td><td style="padding: 8px 10px; color: #fff; font-weight: 600;">Group</td><td style="padding: 8px 10px; color: #fff; font-weight: 600; text-align: right;">Amount</td><td style="padding: 8px 10px; color: #fff; font-weight: 600;">Status</td></tr>
                    {unpaid_rows}
                </table>"""

            tomorrow_preview_section = f"""
            <div class="section-white" style="background: #ffffff; padding: 20px 32px;">
                <h3 class="section-title" style="font-family: 'Space Grotesk', Arial, sans-serif; font-size: 15px; font-weight: 600; color: #0b1c30; margin: 0 0 8px 0;">Tomorrow&#39;s Preview</h3>
                <div style="display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #6b7280;"><strong style="color: #0b1c30;">{preview.session_count}</strong> session{'s' if preview.session_count != 1 else ''}</span>
                    <span style="font-size: 12px; color: #6b7280;"><strong style="color: #0b1c30;">{preview.expected_student_count}</strong> expected student{'s' if preview.expected_student_count != 1 else ''}</span>
                </div>
                {unpaid_section}
            </div>"""
        else:
            tomorrow_preview_section = """
            <div class="section-white" style="background: #ffffff; padding: 20px 32px;">
                <h3 class="section-title" style="font-family: 'Space Grotesk', Arial, sans-serif; font-size: 15px; font-weight: 600; color: #0b1c30; margin: 0 0 8px 0;">Tomorrow&#39;s Preview</h3>
                <p class="empty-state" style="color: #9ca3af; font-style: italic; font-size: 13px; text-align: center; padding: 16px; background: #ffffff;">No sessions scheduled tomorrow.</p>
            </div>"""

        # ── Payment Breakdown (merged & grouped) ─────────────────────────
        payment_details_html = ""
        if aggregates.payments_by_type:
            rows_html = ""
            row_counter = 0
            grand_total = 0.0

            for ptype_group in aggregates.payments_by_type:
                count_label = f"{ptype_group.count} payment{'s' if ptype_group.count != 1 else ''}"
                rows_html += (
                    f'<tr class="group-header">'
                    f'<td colspan="3" style="padding: 8px 10px; font-weight: 600; font-size: 12px; background: #e5eeff;">'
                    f'{ptype_group.payment_type} &mdash; {count_label} &mdash; '
                    f'Subtotal: {ptype_group.subtotal:,.2f} EGP</td></tr>'
                )
                for payment in ptype_group.items:
                    rc = _row_class(row_counter)
                    rows_html += (
                        f'<tr class="{rc}">'
                        f'<td style="padding: 8px 10px; font-size: 12px;">{payment.student_name}</td>'
                        f'<td style="padding: 8px 10px; font-size: 12px;">{payment.group_name}</td>'
                        f'<td style="padding: 8px 10px; font-size: 12px; text-align: right;">{payment.amount:,.2f} EGP</td>'
                        f'</tr>'
                    )
                    row_counter += 1
                grand_total += ptype_group.subtotal

            rows_html += (
                f'<tr class="total-row">'
                f'<td colspan="3" style="padding: 10px; font-weight: 700; text-align: center; font-size: 13px; background: #131b2e; color: #ffffff;">'
                f'Total Revenue: {grand_total:,.2f} EGP</td></tr>'
            )

            payment_details_html = f"""
            <div class="section-default" style="background: #f8f9ff; padding: 20px 32px;">
                <h3 class="section-title" style="font-family: 'Space Grotesk', Arial, sans-serif; font-size: 15px; font-weight: 600; color: #0b1c30; margin: 0 0 12px 0;">Payment Breakdown</h3>
                <table class="data-table" style="width: 100%; border-collapse: collapse; font-size: 12px;">
                    <tr class="header-row">
                        <td style="padding: 8px 10px; color: #fff; font-weight: 600;">Student</td>
                        <td style="padding: 8px 10px; color: #fff; font-weight: 600;">Group</td>
                        <td style="padding: 8px 10px; color: #fff; font-weight: 600; text-align: right;">Amount</td>
                    </tr>
                    {rows_html}
                </table>
            </div>"""
        elif aggregates.payment_details:
            rows_html = ""
            for i, payment in enumerate(aggregates.payment_details):
                rc = _row_class(i)
                rows_html += (
                    f'<tr class="{rc}">'
                    f'<td style="padding: 8px 10px; font-size: 12px;">{payment.student_name}</td>'
                    f'<td style="padding: 8px 10px; font-size: 12px;">{payment.group_name}</td>'
                    f'<td style="padding: 8px 10px; font-size: 12px; text-align: right;">{payment.amount:,.2f} EGP</td>'
                    f'<td style="padding: 8px 10px; font-size: 12px;">{_chip(payment.payment_type)}</td>'
                    f'</tr>'
                )
            payment_details_html = f"""
            <div class="section-default" style="background: #f8f9ff; padding: 20px 32px;">
                <h3 class="section-title" style="font-family: 'Space Grotesk', Arial, sans-serif; font-size: 15px; font-weight: 600; color: #0b1c30; margin: 0 0 12px 0;">Payment Details</h3>
                <table class="data-table" style="width: 100%; border-collapse: collapse; font-size: 12px;">
                    <tr class="header-row">
                        <td style="padding: 8px 10px; color: #fff; font-weight: 600;">Student</td>
                        <td style="padding: 8px 10px; color: #fff; font-weight: 600;">Group</td>
                        <td style="padding: 8px 10px; color: #fff; font-weight: 600; text-align: right;">Amount</td>
                        <td style="padding: 8px 10px; color: #fff; font-weight: 600;">Type</td>
                    </tr>
                    {rows_html}
                </table>
            </div>"""
        else:
            payment_details_html = """<div class="section-default" style="background: #f8f9ff; padding: 20px 32px;"><p class="empty-state" style="color: #9ca3af; font-style: italic; font-size: 13px; text-align: center; padding: 16px; background: #ffffff;">No payments recorded today.</p></div>"""

        # ── Session Attendance Details ────────────────────────────────────
        session_details_html = ""
        if aggregates.session_details:
            session_rows = ""
            for i, s in enumerate(aggregates.session_details):
                rc = _row_class(i)
                present_list = [n.strip() for n in s.student_names_present.split(",") if n.strip()] if s.student_names_present else []
                absent_list = [n.strip() for n in s.student_names_absent.split(",") if n.strip()] if s.student_names_absent else []

                display_time = s.session_time or "—"

                session_rows += (
                    f'<tr class="{rc}">'
                    f'<td style="padding: 8px 10px; font-size: 12px;">{s.instructor_name}</td>'
                    f'<td style="padding: 8px 10px; font-size: 12px; text-align: center;">{display_time}</td>'
                    f'<td style="padding: 8px 10px; font-size: 12px; text-align: center;">{s.present_count}</td>'
                    f'<td style="padding: 8px 10px; font-size: 12px; text-align: center;">{s.absent_count}</td>'
                    f'<td style="padding: 8px 10px; font-size: 12px; text-align: center;">{s.cancelled_count}</td>'
                    f'<td style="padding: 8px 10px; font-size: 12px;">{_to_html_list(present_list) if present_list else "—"}</td>'
                    f'<td style="padding: 8px 10px; font-size: 12px;">{_to_html_list(absent_list) if absent_list else "—"}</td>'
                    f'</tr>'
                )
            session_details_html = f"""
            <div class="section-white" style="background: #ffffff; padding: 20px 32px;">
                <h3 class="section-title" style="font-family: 'Space Grotesk', Arial, sans-serif; font-size: 15px; font-weight: 600; color: #0b1c30; margin: 0 0 12px 0;">Session Attendance Details</h3>
                <table class="data-table" style="width: 100%; border-collapse: collapse; font-size: 12px;">
                    <tr class="header-row">
                        <td style="padding: 8px 10px; color: #fff; font-weight: 600;">Instructor</td>
                        <td style="padding: 8px 10px; color: #fff; font-weight: 600; text-align: center;">Time</td>
                        <td style="padding: 8px 10px; color: #fff; font-weight: 600; text-align: center;">P</td>
                        <td style="padding: 8px 10px; color: #fff; font-weight: 600; text-align: center;">A</td>
                        <td style="padding: 8px 10px; color: #fff; font-weight: 600; text-align: center;">C</td>
                        <td style="padding: 8px 10px; color: #fff; font-weight: 600;">Present</td>
                        <td style="padding: 8px 10px; color: #fff; font-weight: 600;">Absent</td>
                    </tr>
                    {session_rows}
                </table>
            </div>"""
        else:
            session_details_html = """<div class="section-white" style="background: #ffffff; padding: 20px 32px;"><p class="empty-state" style="color: #9ca3af; font-style: italic; font-size: 13px; text-align: center; padding: 16px; background: #ffffff;">No completed sessions today.</p></div>"""

        # ── Instructor Summary ───────────────────────────────────────────
        instructor_summary_html = ""
        if aggregates.instructor_summary:
            instructor_rows = ""
            for i, item in enumerate(aggregates.instructor_summary):
                rc = _row_class(i)
                instructor_rows += (
                    f'<tr class="{rc}">'
                    f'<td style="padding: 8px 10px; font-size: 12px;">{item.instructor_name}</td>'
                    f'<td style="padding: 8px 10px; font-size: 12px; text-align: right;">{item.session_count}</td>'
                    f'</tr>'
                )
            instructor_summary_html = f"""
            <div class="section-default" style="background: #f8f9ff; padding: 20px 32px;">
                <h3 class="section-title" style="font-family: 'Space Grotesk', Arial, sans-serif; font-size: 15px; font-weight: 600; color: #0b1c30; margin: 0 0 12px 0;">Instructor Summary</h3>
                <table class="data-table" style="width: 100%; border-collapse: collapse; font-size: 12px;">
                    <tr class="header-row">
                        <td style="padding: 8px 10px; color: #fff; font-weight: 600;">Instructor</td>
                        <td style="padding: 8px 10px; color: #fff; font-weight: 600; text-align: right;">Sessions</td>
                    </tr>
                    {instructor_rows}
                </table>
            </div>"""
        else:
            instructor_summary_html = """<div class="section-default" style="background: #f8f9ff; padding: 20px 32px;"><p class="empty-state" style="color: #9ca3af; font-style: italic; font-size: 13px; text-align: center; padding: 16px; background: #ffffff;">No instructor summary available.</p></div>"""

        return {
            "date": target_date.isoformat(),
            "total_revenue": f"{aggregates.total_revenue:,.2f}",
            "new_enrollments": aggregates.new_enrollments,
            "sessions_held": aggregates.sessions_held,
            "absent_count": aggregates.absent_count,
            "payment_count": aggregates.payment_count,
            "payment_methods": payment_methods_str,
            "payment_details": payment_details_html,
            "instructors_list": instructors_str,
            "attendance_rate": f"{aggregates.attendance_rate:.1%}",
            "session_details": session_details_html,
            "instructor_summary": instructor_summary_html,
            "payments_by_type": "",
            "debtors_section": debtors_section,
            "cumulative_debtors_section": cumulative_debtors_section,
            "tomorrow_preview_section": tomorrow_preview_section,
        }

    # ── Private Helpers ──────────────────────────────────────────────────
    
    def _fetch_daily_aggregates(self, target_date: date) -> DailyReportAggregateDTO:
        """Fetch daily metrics with debtors data and tomorrow preview."""
        with unit_of_work() as uow:
            repo = ReportsRepository(uow.session)
            aggregates = repo.get_daily_aggregates(target_date)

            # Fetch session-3 unpaid attendees (yesterday alert)
            try:
                aggregates.today_unpaid_attendees = repo.fetch_session3_unpaid(target_date)
            except Exception as e:
                logger.warning(f"Could not fetch session-3 unpaid attendees: {e}")
                aggregates.today_unpaid_attendees = []

            # Fetch cumulative 3+ sessions unpaid attendees
            try:
                aggregates.cumulative_unpaid_debtors = repo.fetch_cumulative_unpaid(target_date)
            except Exception as e:
                logger.warning(f"Could not fetch cumulative unpaid attendees: {e}")
                aggregates.cumulative_unpaid_debtors = []

            # Fetch tomorrow preview via repo
            try:
                aggregates.tomorrow_preview = repo.fetch_tomorrow_preview(target_date)
            except Exception as e:
                logger.warning(f"Could not fetch tomorrow preview: {e}")

            return aggregates

    
    def _fetch_weekly_aggregates(self, week_start: date, week_end: date) -> PeriodReportAggregateDTO:
        """Fetch enriched weekly metrics."""
        with unit_of_work() as uow:
            return ReportsRepository(uow.session).get_weekly_aggregates(week_start, week_end)
    
    def _fetch_monthly_aggregates(self, month_start: date, month_end: date) -> PeriodReportAggregateDTO:
        """Fetch enriched monthly metrics."""
        with unit_of_work() as uow:
            return ReportsRepository(uow.session).get_monthly_aggregates(month_start, month_end)
    
    # ── Bulk Marketing (now sends to all admins via email) ──────────────
    
    def send_bulk(
        self, parent_ids: list[int], template_name: str, extra_vars: dict, #TODO remove Dict and write a typed DTO class
        background_tasks
    ) -> int:
        """Queue email messages to all admins. Returns queued count."""
        template = self._get_template_by_name(template_name)
        if not template or not template.is_active:
            return 0
        
        # Get notification recipients (fallback handled automatically by base service)
        recipients = self._resolve_notification_recipients("bulk")
        
        count = 0
        for email, recipient_id, recipient_type in recipients:
            variables = extra_vars.copy()
            variables.setdefault("parent_name", "Admin")
            
            background_tasks.add_task(
                self._dispatch, template, "EMAIL", recipient_type,
                recipient_id, email, variables
            )
            count += 1
        

        return count
