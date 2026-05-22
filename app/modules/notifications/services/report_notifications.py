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
from app.modules.notifications.repositories.notification_repository import NotificationRepository
from app.modules.notifications.repositories.reports_repository import ReportsRepository
from app.modules.notifications.schemas.report_dto import (
    DailyReportAggregateDTO,
    PaymentTypeGroup,
    SessionDetailItem,
    InstructorSummaryItem,
)


class PeriodReportAggregateDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total_revenue: Decimal = Decimal("0.00")
    new_students: int = 0
    attendance_rate: float = 0.0
    new_enrollments: int = 0
    active_students: int = 0


logger = logging.getLogger(__name__)


class ReportNotificationService(BaseNotificationService):
    """Handles: daily, weekly, monthly business reports."""
    
    def __init__(self, repo: NotificationRepository):
        super().__init__(repo)
    
    # ── Scheduled Report Methods ─────────────────────────────────────────
    
    async def send_daily_report(self, target_date: Optional[date] = None) -> None:
        """Daily business summary to all admins."""
        template = self._repo.get_template_by_name("daily_report")
        if not template or not template.is_active:
            logger.warning("daily_report template not found or inactive - skipping.")
            return
        
        # Get notification recipients (fallback handled automatically by base service)
        recipients = self._resolve_notification_recipients("daily_report")
        
        today = target_date or date.today()
        aggregates = self._fetch_daily_aggregates(today)
        
        # Format payment methods for display
        payment_methods_str = ", ".join(
            [f"{method}: {count}" for method, count in aggregates.payment_methods.items()]
        ) if aggregates.payment_methods else "N/A"
        
        # Format instructors list
        instructors_str = ", ".join(aggregates.instructors_list) if aggregates.instructors_list else "N/A"
        
        # Format payment details for template
        payment_details_html = ""
        if aggregates.payment_details:
            payment_rows = ""
            for payment in aggregates.payment_details:
                payment_rows += f"<tr><td>{payment.student_name}</td><td>{payment.group_name}</td><td>{payment.amount:.2f} EGP</td><td>{payment.payment_type}</td></tr>"
            payment_details_html = f"""
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px; border: 1px solid #000;">
                <thead>
                    <tr style="background: #333333; color: white;">
                        <th style="padding: 10px; text-align: left; border: 1px solid #000;">Student</th>
                        <th style="padding: 10px; text-align: left; border: 1px solid #000;">Group</th>
                        <th style="padding: 10px; text-align: right; border: 1px solid #000;">Amount</th>
                        <th style="padding: 10px; text-align: left; border: 1px solid #000;">Type</th>
                    </tr>
                </thead>
                <tbody>
                    {payment_rows}
                </tbody>
            </table>
            """
        else:
            payment_details_html = "<p style='color: #000; font-style: italic;'>No payments recorded today.</p>"
        
        # Build session details HTML table
        session_details_html = ""
        if aggregates.session_details:
            session_rows = ""
            for session_item in aggregates.session_details:
                session_rows += (
                    f"<tr>"
                    f"<td>{session_item.instructor_name}</td>"
                    f"<td>{session_item.session_time}</td>"
                    f"<td>{session_item.present_count}</td>"
                    f"<td>{session_item.absent_count}</td>"
                    f"<td>{session_item.cancelled_count}</td>"
                    f"<td>{session_item.student_names_present}</td>"
                    f"<td>{session_item.student_names_absent}</td>"
                    f"</tr>"
                )
            session_details_html = f"""
            <h3 style="color: #000; margin-top: 20px;">Session Attendance Details</h3>
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px; border: 1px solid #000;">
                <thead>
                    <tr style="background: #333333; color: white;">
                        <th style="padding: 8px; text-align: left; border: 1px solid #000;">Instructor</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #000;">Time</th>
                        <th style="padding: 8px; text-align: center; border: 1px solid #000;">Present</th>
                        <th style="padding: 8px; text-align: center; border: 1px solid #000;">Absent</th>
                        <th style="padding: 8px; text-align: center; border: 1px solid #000;">Cancelled</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #000;">Students Present</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #000;">Students Absent</th>
                    </tr>
                </thead>
                <tbody>
                    {session_rows}
                </tbody>
            </table>
            """
        else:
            session_details_html = "<p style='color: #000; font-style: italic;'>No completed sessions today.</p>"

        # Build instructor summary HTML table
        instructor_summary_html = ""
        if aggregates.instructor_summary:
            instructor_rows = ""
            for item in aggregates.instructor_summary:
                instructor_rows += f"<tr><td>{item.instructor_name}</td><td>{item.session_count}</td></tr>"
            instructor_summary_html = f"""
            <h3 style="color: #000; margin-top: 20px;">Instructor Summary</h3>
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px; border: 1px solid #000;">
                <thead>
                    <tr style="background: #333333; color: white;">
                        <th style="padding: 8px; text-align: left; border: 1px solid #000;">Instructor</th>
                        <th style="padding: 8px; text-align: center; border: 1px solid #000;">Sessions</th>
                    </tr>
                </thead>
                <tbody>
                    {instructor_rows}
                </tbody>
            </table>
            """
        else:
            instructor_summary_html = "<p style='color: #000; font-style: italic;'>No instructor summary available.</p>"

        # Build payments by type HTML sub-tables
        payments_by_type_html = ""
        if aggregates.payments_by_type:
            payments_by_type_html = "<h3 style='color: #000; margin-top: 20px;'>Payments by Type</h3>"
            for ptype_group in aggregates.payments_by_type:
                sub_rows = ""
                for payment in ptype_group.items:
                    sub_rows += f"<tr><td>{payment.student_name}</td><td>{payment.group_name}</td><td style='text-align: right;'>{payment.amount:.2f} EGP</td></tr>"
                payments_by_type_html += f"""
                <h4 style="color: #000; margin: 10px 0 5px 0;">{ptype_group.payment_type} (Subtotal: {ptype_group.subtotal:.2f} EGP — {ptype_group.count} payments)</h4>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px; border: 1px solid #000;">
                    <thead>
                        <tr style="background: #555555; color: white;">
                            <th style="padding: 6px; text-align: left; border: 1px solid #000;">Student</th>
                            <th style="padding: 6px; text-align: left; border: 1px solid #000;">Group</th>
                            <th style="padding: 6px; text-align: right; border: 1px solid #000;">Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sub_rows}
                    </tbody>
                </table>
                """
        else:
            payments_by_type_html = ""

        variables = {
            "date": today.strftime("%Y-%m-%d"),
            "total_revenue": f"{aggregates.total_revenue:.2f}",
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
            "payments_by_type": payments_by_type_html,
        }
        
        # Generate PDF attachment
        pdf_bytes = None
        try:
            from app.modules.notifications.pdf.daily_report_pdf import generate_daily_report_pdf
            pdf_bytes = generate_daily_report_pdf(
                date_str=today.strftime("%Y-%m-%d"),
                aggregates=aggregates
            )
            logger.info(f"Generated daily report PDF for {today}")
        except Exception as e:
            logger.error(f"Failed to generate daily report PDF: {e}")
        
        # Prepare attachments
        attachments = None
        if pdf_bytes:
            filename = f"daily_report_{today.strftime('%Y-%m-%d')}.pdf"
            attachments = [(filename, pdf_bytes, "application/pdf")]
        
        # Send to all enabled recipients with PDF attachment
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(
                template, "EMAIL", recipient_type, recipient_id, email,
                variables, attachments=attachments
            )
    
    async def send_weekly_report(self) -> None:
        """Weekly business summary to all admins."""
        template = self._repo.get_template_by_name("weekly_report")
        if not template or not template.is_active:
            logger.warning("weekly_report template not found or inactive - skipping.")
            return
        
        # Get notification recipients (fallback handled automatically by base service)
        recipients = self._resolve_notification_recipients("weekly_report")
        
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = today
        
        aggregates = self._fetch_weekly_aggregates(week_start, week_end)
        
        variables = {
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d"),
            "total_revenue": f"{aggregates.total_revenue:.2f}",
            "new_students": aggregates.new_students,
            "attendance_rate": f"{aggregates.attendance_rate:.1f}",
        }

        # Send to all enabled recipients (admins + additional recipients)
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)

    async def send_monthly_report(self) -> None:
        """Monthly business summary to all admins."""
        template = self._repo.get_template_by_name("monthly_report")
        if not template or not template.is_active:
            logger.warning("monthly_report template not found or inactive - skipping.")
            return

        # Get notification recipients (fallback handled automatically by base service)
        recipients = self._resolve_notification_recipients("monthly_report")

        today = date.today()
        month_start = today.replace(day=1)

        aggregates = self._fetch_monthly_aggregates(month_start, today)

        variables = {
            "month": today.strftime("%B %Y"),
            "total_revenue": f"{aggregates.total_revenue:.2f}",
            "new_enrollments": aggregates.new_enrollments,
            "active_students": aggregates.active_students,
        }
        
        # Send to all enabled recipients (admins + additional recipients)
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)
    
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
        template = self._repo.get_template_by_name("daily_report")
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
        )

    def _build_variables(
        self, aggregates: DailyReportAggregateDTO, target_date: date
    ) -> dict:
        """Build the template variables dict (shared between email modes)."""
        payment_methods_str = ", ".join(
            [f"{method}: {count}" for method, count in aggregates.payment_methods.items()]
        ) if aggregates.payment_methods else "N/A"

        instructors_str = ", ".join(aggregates.instructors_list) if aggregates.instructors_list else "N/A"

        payment_details_html = ""
        if aggregates.payment_details:
            payment_rows = ""
            for payment in aggregates.payment_details:
                payment_rows += f"<tr><td>{payment.student_name}</td><td>{payment.group_name}</td><td>{payment.amount:.2f} EGP</td><td>{payment.payment_type}</td></tr>"
            payment_details_html = f"""
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px; border: 1px solid #000;">
                <thead><tr style="background: #333333; color: white;">
                    <th style="padding: 10px; text-align: left; border: 1px solid #000;">Student</th>
                    <th style="padding: 10px; text-align: left; border: 1px solid #000;">Group</th>
                    <th style="padding: 10px; text-align: right; border: 1px solid #000;">Amount</th>
                    <th style="padding: 10px; text-align: left; border: 1px solid #000;">Type</th>
                </tr></thead>
                <tbody>{payment_rows}</tbody>
            </table>"""
        else:
            payment_details_html = "<p style='color: #000; font-style: italic;'>No payments recorded today.</p>"

        session_details_html = ""
        if aggregates.session_details:
            session_rows = ""
            for session_item in aggregates.session_details:
                session_rows += (
                    f"<tr><td>{session_item.instructor_name}</td><td>{session_item.session_time}</td>"
                    f"<td>{session_item.present_count}</td><td>{session_item.absent_count}</td>"
                    f"<td>{session_item.cancelled_count}</td>"
                    f"<td>{session_item.student_names_present}</td><td>{session_item.student_names_absent}</td></tr>"
                )
            session_details_html = f"""
            <h3 style="color: #000; margin-top: 20px;">Session Attendance Details</h3>
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px; border: 1px solid #000;">
                <thead><tr style="background: #333333; color: white;">
                    <th style="padding: 8px; text-align: left; border: 1px solid #000;">Instructor</th>
                    <th style="padding: 8px; text-align: left; border: 1px solid #000;">Time</th>
                    <th style="padding: 8px; text-align: center; border: 1px solid #000;">Present</th>
                    <th style="padding: 8px; text-align: center; border: 1px solid #000;">Absent</th>
                    <th style="padding: 8px; text-align: center; border: 1px solid #000;">Cancelled</th>
                    <th style="padding: 8px; text-align: left; border: 1px solid #000;">Students Present</th>
                    <th style="padding: 8px; text-align: left; border: 1px solid #000;">Students Absent</th>
                </tr></thead>
                <tbody>{session_rows}</tbody>
            </table>"""
        else:
            session_details_html = "<p style='color: #000; font-style: italic;'>No completed sessions today.</p>"

        instructor_summary_html = ""
        if aggregates.instructor_summary:
            instructor_rows = ""
            for item in aggregates.instructor_summary:
                instructor_rows += f"<tr><td>{item.instructor_name}</td><td>{item.session_count}</td></tr>"
            instructor_summary_html = f"""
            <h3 style="color: #000; margin-top: 20px;">Instructor Summary</h3>
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px; border: 1px solid #000;">
                <thead><tr style="background: #333333; color: white;">
                    <th style="padding: 8px; text-align: left; border: 1px solid #000;">Instructor</th>
                    <th style="padding: 8px; text-align: center; border: 1px solid #000;">Sessions</th>
                </tr></thead>
                <tbody>{instructor_rows}</tbody>
            </table>"""
        else:
            instructor_summary_html = "<p style='color: #000; font-style: italic;'>No instructor summary available.</p>"

        payments_by_type_html = ""
        if aggregates.payments_by_type:
            payments_by_type_html = "<h3 style='color: #000; margin-top: 20px;'>Payments by Type</h3>"
            for ptype_group in aggregates.payments_by_type:
                sub_rows = ""
                for payment in ptype_group.items:
                    sub_rows += f"<tr><td>{payment.student_name}</td><td>{payment.group_name}</td><td style='text-align: right;'>{payment.amount:.2f} EGP</td></tr>"
                payments_by_type_html += f"""
                <h4 style="color: #000; margin: 10px 0 5px 0;">{ptype_group.payment_type} (Subtotal: {ptype_group.subtotal:.2f} EGP — {ptype_group.count} payments)</h4>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px; border: 1px solid #000;">
                    <thead><tr style="background: #555555; color: white;">
                        <th style="padding: 6px; text-align: left; border: 1px solid #000;">Student</th>
                        <th style="padding: 6px; text-align: left; border: 1px solid #000;">Group</th>
                        <th style="padding: 6px; text-align: right; border: 1px solid #000;">Amount</th>
                    </tr></thead>
                    <tbody>{sub_rows}</tbody>
                </table>"""
        else:
            payments_by_type_html = ""

        return {
            "date": target_date.isoformat(),
            "total_revenue": f"{aggregates.total_revenue:.2f}",
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
            "payments_by_type": payments_by_type_html,
        }

    # ── Private Helpers ──────────────────────────────────────────────────
    
    def _fetch_daily_aggregates(self, target_date: date) -> DailyReportAggregateDTO:
        """Fetch daily metrics with enhanced data for rich reporting."""
        from app.db.connection import get_session
        with get_session() as session:
            repo = ReportsRepository(session)
            return repo.get_daily_aggregates(target_date)
    
    def _fetch_weekly_aggregates(self, week_start: date, week_end: date) -> PeriodReportAggregateDTO:
        """Fetch weekly metrics."""
        total_revenue = Decimal("0.00")
        new_students = 0
        attendance_rate = 0.0

        try:
            from app.modules.analytics.services.financial_service import FinancialAnalyticsService
            fin_svc = FinancialAnalyticsService()
            revenue_data = fin_svc.get_revenue_by_date(week_start, week_end)
            total_revenue = sum(r.net_revenue for r in revenue_data)
        except Exception as e:
            logger.warning(f"Could not fetch weekly revenue: {e}")

        try:
            from app.db.connection import get_session
            from sqlmodel import select, func
            from app.modules.enrollments.models.enrollment_models import Enrollment
            with get_session() as session:
                stmt = select(func.count()).select_from(Enrollment).where(
                    Enrollment.enrolled_at >= week_start,
                    Enrollment.enrolled_at <= week_end,
                )
                new_students = session.exec(stmt).one() or 0
        except Exception as e:
            logger.warning(f"Could not fetch weekly new students: {e}")

        try:
            from app.modules.analytics.services.bi_service import BIAnalyticsService
            bi_svc = BIAnalyticsService()
            retention_data = bi_svc.get_retention_metrics()
            if retention_data:
                total_active = sum(r.active_count for r in retention_data)
                total_all = sum(r.total_enrollments for r in retention_data)
                attendance_rate = (total_active / total_all * 100) if total_all > 0 else 0.0
        except Exception as e:
            logger.warning(f"Could not fetch weekly attendance rate: {e}")

        return PeriodReportAggregateDTO(
            total_revenue=total_revenue,
            new_students=new_students,
            attendance_rate=attendance_rate,
        )
    
    def _fetch_monthly_aggregates(self, month_start: date, month_end: date) -> PeriodReportAggregateDTO:
        """Fetch monthly metrics."""
        total_revenue = Decimal("0.00")
        new_enrollments = 0
        active_students = 0

        try:
            from app.modules.analytics.services.financial_service import FinancialAnalyticsService
            fin_svc = FinancialAnalyticsService()
            revenue_data = fin_svc.get_revenue_by_date(month_start, month_end)
            total_revenue = sum(r.net_revenue for r in revenue_data)
        except Exception as e:
            logger.warning(f"Could not fetch monthly revenue: {e}")

        try:
            from app.db.connection import get_session
            from sqlmodel import select, func
            from app.modules.enrollments.models.enrollment_models import Enrollment
            with get_session() as session:
                new_stmt = select(func.count()).select_from(Enrollment).where(
                    Enrollment.enrolled_at >= month_start,
                    Enrollment.enrolled_at <= month_end,
                )
                new_enrollments = session.exec(new_stmt).one() or 0

                active_stmt = select(func.count()).select_from(Enrollment).where(
                    Enrollment.status == "active"
                )
                active_students = session.exec(active_stmt).one() or 0
        except Exception as e:
            logger.warning(f"Could not fetch monthly enrollment stats: {e}")

        return PeriodReportAggregateDTO(
            total_revenue=total_revenue,
            new_enrollments=new_enrollments,
            active_students=active_students,
        )
    
    # ── Bulk Marketing (now sends to all admins via email) ──────────────
    
    def send_bulk(
        self, parent_ids: list[int], template_name: str, extra_vars: dict, #TODO remove Dict and write a typed DTO class
        background_tasks
    ) -> int:
        """Queue email messages to all admins. Returns queued count."""
        template = self._repo.get_template_by_name(template_name)
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
