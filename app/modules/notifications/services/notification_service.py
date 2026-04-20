"""
app/modules/notifications/services/notification_service.py
──────────────────────────────────────────────────────────
Main notification orchestrator.

Responsibilities:
 - Template rendering ({{variable}} substitution)
 - Recipient contact resolution from DB
 - BackgroundTask dispatch (non-blocking for transactional sends)
 - Notification log persistence
 - Scheduled report generation via analytics services
"""
import logging
from datetime import date, timedelta
from typing import Optional, Tuple, List
from fastapi import BackgroundTasks
from sqlmodel import select

from app.modules.notifications.interfaces.i_notification_repository import INotificationRepository
from app.modules.notifications.dispatchers.whatsapp_dispatcher import TwilioWhatsAppDispatcher
from app.modules.notifications.dispatchers.email_dispatcher import GmailEmailDispatcher
from app.modules.notifications.models.notification_template import NotificationTemplate
from app.modules.notifications.models.notification_subscriber import NotificationSubscriber

from app.modules.crm.models.parent_models import Parent
from app.modules.crm.models.link_models import StudentParent
from app.modules.crm.models.student_models import Student

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Main notification orchestrator.
    """

    def __init__(self, repo: INotificationRepository):
        self._repo = repo
        self._whatsapp = TwilioWhatsAppDispatcher()
        self._email = GmailEmailDispatcher()

    # ── Transactional (called by other services) ─────────────────────────

    def notify_absence(
        self,
        student_id: int,
        session_name: str,
        session_date: str,
        background_tasks: BackgroundTasks,
    ) -> None:
        """Queues an absence alert to the student's primary parent. Non-blocking."""
        background_tasks.add_task(
            self._process_absence_notification,
            student_id, session_name, session_date,
        )

    def notify_enrollment(
        self,
        enrollment_id: int,
        student_id: int,
        group_id: int,
        background_tasks: BackgroundTasks,
    ) -> None:
        """Queues an enrollment confirmation to the student's primary parent."""
        background_tasks.add_task(
            self._process_enrollment_notification,
            enrollment_id, student_id, group_id,
        )

    def notify_payment_receipt(
        self,
        receipt_id: int,
        student_id: int,
        amount: str,
        receipt_number: str,
        background_tasks: BackgroundTasks,
    ) -> None:
        """Queues a payment receipt notification to the parent."""
        background_tasks.add_task(
            self._process_receipt_notification,
            receipt_id, student_id, amount, receipt_number,
        )

    # ── Scheduled Reports ─────────────────────────────────────────────────

    async def send_daily_report(self) -> None:
        """Builds and emails the daily business summary to all DAILY subscribers."""
        logger.info("Sending daily business report.")
        try:
            template = self._repo.get_template_by_name("daily_report")
            if not template or not template.is_active:
                logger.warning("daily_report template not found or inactive — skipping.")
                return

            subscribers = self._repo.get_report_subscribers("DAILY")
            if not subscribers:
                logger.info("No DAILY subscribers found — skipping.")
                return

            today = date.today()
            # Collect aggregates from analytics services (fresh sessions internally)
            aggregates = self._fetch_daily_aggregates(today)

            variables = {
                "date": today.strftime("%Y-%m-%d"),
                "total_revenue": f"{aggregates['total_revenue']:.2f}",
                "new_enrollments": aggregates["new_enrollments"],
                "sessions_held": aggregates["sessions_held"],
                "absent_count": aggregates["absent_count"],
            }

            await self._dispatch_report_to_subscribers(template, subscribers, variables)
        except Exception as e:
            logger.error("Daily report failed: %s", e)

    async def send_weekly_report(self) -> None:
        """Builds and emails the weekly business summary to all WEEKLY subscribers."""
        logger.info("Sending weekly business report.")
        try:
            template = self._repo.get_template_by_name("weekly_report")
            if not template or not template.is_active:
                logger.warning("weekly_report template not found or inactive — skipping.")
                return

            subscribers = self._repo.get_report_subscribers("WEEKLY")
            if not subscribers:
                logger.info("No WEEKLY subscribers found — skipping.")
                return

            today = date.today()
            week_start = today - timedelta(days=today.weekday())  # Monday
            week_end = today

            aggregates = self._fetch_weekly_aggregates(week_start, week_end)

            variables = {
                "week_start": week_start.strftime("%Y-%m-%d"),
                "week_end": week_end.strftime("%Y-%m-%d"),
                "total_revenue": f"{aggregates['total_revenue']:.2f}",
                "new_students": aggregates["new_students"],
                "attendance_rate": f"{aggregates['attendance_rate']:.1f}",
            }

            await self._dispatch_report_to_subscribers(template, subscribers, variables)
        except Exception as e:
            logger.error("Weekly report failed: %s", e)

    async def send_monthly_report(self) -> None:
        """Builds and emails the monthly business summary to all MONTHLY subscribers."""
        logger.info("Sending monthly business report.")
        try:
            template = self._repo.get_template_by_name("monthly_report")
            if not template or not template.is_active:
                logger.warning("monthly_report template not found or inactive — skipping.")
                return

            subscribers = self._repo.get_report_subscribers("MONTHLY")
            if not subscribers:
                logger.info("No MONTHLY subscribers found — skipping.")
                return

            today = date.today()
            # First day of current month to today
            month_start = today.replace(day=1)
            aggregates = self._fetch_monthly_aggregates(month_start, today)

            variables = {
                "month": today.strftime("%B %Y"),
                "total_revenue": f"{aggregates['total_revenue']:.2f}",
                "new_enrollments": aggregates["new_enrollments"],
                "active_students": aggregates["active_students"],
            }

            await self._dispatch_report_to_subscribers(template, subscribers, variables)
        except Exception as e:
            logger.error("Monthly report failed: %s", e)

    # ── Bulk Marketing ────────────────────────────────────────────────────

    def send_bulk(
        self,
        parent_ids: list[int],
        template_name: str,
        extra_vars: dict,
        background_tasks: BackgroundTasks,
    ) -> int:
        """Queues WhatsApp messages to a list of parents. Returns queued count."""
        template = self._repo.get_template_by_name(template_name)
        if not template or not template.is_active:
            return 0

        count = 0
        for pid in parent_ids:
            background_tasks.add_task(self._process_bulk_item, pid, template, extra_vars)
            count += 1
        return count

    # ── Analytics Data Fetchers ──────────────────────────────────────────

    def _fetch_daily_aggregates(self, target_date: date) -> dict:
        """Fetches aggregated daily metrics from analytics services."""
        from app.modules.analytics.services.financial_service import FinancialAnalyticsService
        from app.modules.analytics.services.academic_service import AcademicAnalyticsService

        total_revenue = 0.0
        new_enrollments = 0
        sessions_held = 0
        absent_count = 0

        try:
            fin_svc = FinancialAnalyticsService()
            revenue_data = fin_svc.get_revenue_by_date(target_date, target_date)
            total_revenue = sum(r.net_revenue for r in revenue_data)
        except Exception as e:
            logger.warning("Could not fetch daily revenue: %s", e)

        try:
            academic_svc = AcademicAnalyticsService()
            summary = academic_svc.get_dashboard_summary()
            sessions_held = summary.today_sessions_count
            # Count total absent from today's sessions
            absent_count = sum(s.absent for s in summary.sessions)
        except Exception as e:
            logger.warning("Could not fetch daily academic summary: %s", e)

        try:
            from app.db.connection import get_session
            from sqlmodel import select, func
            from app.modules.enrollments.models.enrollment_models import Enrollment
            with get_session() as session:
                stmt = select(func.count()).select_from(Enrollment).where(
                    Enrollment.enrolled_at >= target_date,
                    Enrollment.enrolled_at < target_date + timedelta(days=1),
                )
                new_enrollments = session.exec(stmt).one() or 0
        except Exception as e:
            logger.warning("Could not fetch new enrollments count: %s", e)

        return {
            "total_revenue": total_revenue,
            "new_enrollments": new_enrollments,
            "sessions_held": sessions_held,
            "absent_count": absent_count,
        }

    def _fetch_weekly_aggregates(self, week_start: date, week_end: date) -> dict:
        """Fetches aggregated weekly metrics."""
        from app.modules.analytics.services.financial_service import FinancialAnalyticsService

        total_revenue = 0.0
        new_students = 0
        attendance_rate = 0.0

        try:
            fin_svc = FinancialAnalyticsService()
            revenue_data = fin_svc.get_revenue_by_date(week_start, week_end)
            total_revenue = sum(r.net_revenue for r in revenue_data)
        except Exception as e:
            logger.warning("Could not fetch weekly revenue: %s", e)

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
            logger.warning("Could not fetch weekly new students: %s", e)

        try:
            from app.modules.analytics.services.bi_service import BIAnalyticsService
            bi_svc = BIAnalyticsService()
            retention_data = bi_svc.get_retention_metrics()
            if retention_data:
                total_active = sum(r.active_count for r in retention_data)
                total_all = sum(r.total_enrollments for r in retention_data)
                attendance_rate = (total_active / total_all * 100) if total_all > 0 else 0.0
        except Exception as e:
            logger.warning("Could not fetch weekly attendance rate: %s", e)

        return {
            "total_revenue": total_revenue,
            "new_students": new_students,
            "attendance_rate": attendance_rate,
        }

    def _fetch_monthly_aggregates(self, month_start: date, month_end: date) -> dict:
        """Fetches aggregated monthly metrics."""
        from app.modules.analytics.services.financial_service import FinancialAnalyticsService

        total_revenue = 0.0
        new_enrollments = 0
        active_students = 0

        try:
            fin_svc = FinancialAnalyticsService()
            revenue_data = fin_svc.get_revenue_by_date(month_start, month_end)
            total_revenue = sum(r.net_revenue for r in revenue_data)
        except Exception as e:
            logger.warning("Could not fetch monthly revenue: %s", e)

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
            logger.warning("Could not fetch monthly enrollment stats: %s", e)

        return {
            "total_revenue": total_revenue,
            "new_enrollments": new_enrollments,
            "active_students": active_students,
        }

    # ── Asynchronous Processors ──────────────────────────────────────────

    async def _process_absence_notification(
        self, student_id: int, session_name: str, session_date: str
    ) -> None:
        template = self._repo.get_template_by_name("absence_alert")
        if not template or not template.is_active:
            return

        phone, parent_id, parent_name, student_name = self._resolve_contact_info(student_id)
        if not phone or not parent_id:
            return

        variables = {
            "parent_name": parent_name,
            "student_name": student_name,
            "session_name": session_name,
            "session_date": session_date,
        }
        await self._dispatch_internal(
            template, "WHATSAPP", "PARENT", parent_id, phone, variables
        )

    async def _process_enrollment_notification(
        self, enrollment_id: int, student_id: int, group_id: int
    ) -> None:
        template = self._repo.get_template_by_name("enrollment_confirmation")
        if not template or not template.is_active:
            return

        phone, parent_id, parent_name, student_name = self._resolve_contact_info(student_id)
        if not phone or not parent_id:
            return

        # Resolve group and course names
        group_name = f"Group {group_id}"
        course_name = "N/A"
        try:
            from app.db.connection import get_session
            from app.modules.academics.models.group_models import Group
            from app.modules.academics.models.course_models import Course
            with get_session() as session:
                group = session.get(Group, group_id)
                if group:
                    group_name = group.name
                    course = session.get(Course, group.course_id)
                    if course:
                        course_name = course.name
        except Exception as e:
            logger.warning("Could not resolve group/course names for enrollment notification: %s", e)

        variables = {
            "parent_name": parent_name,
            "student_name": student_name,
            "group_name": group_name,
            "course_name": course_name,
        }
        await self._dispatch_internal(
            template, "WHATSAPP", "PARENT", parent_id, phone, variables
        )

    async def _process_receipt_notification(
        self, receipt_id: int, student_id: int, amount: str, receipt_number: str
    ) -> None:
        template = self._repo.get_template_by_name("payment_receipt")
        if not template or not template.is_active:
            return

        phone, parent_id, parent_name, student_name = self._resolve_contact_info(student_id)
        if not phone or not parent_id:
            return

        variables = {
            "parent_name": parent_name,
            "student_name": student_name,
            "amount": amount,
            "receipt_number": receipt_number,
        }
        await self._dispatch_internal(
            template, "WHATSAPP", "PARENT", parent_id, phone, variables
        )

    async def _process_bulk_item(
        self, parent_id: int, template: NotificationTemplate, extra_vars: dict
    ) -> None:
        parent = self._repo._session.get(Parent, parent_id)
        if not parent or not parent.phone_primary:
            return

        variables = extra_vars.copy()
        variables.setdefault("parent_name", parent.full_name)
        await self._dispatch_internal(
            template, "WHATSAPP", "PARENT", parent_id, parent.phone_primary, variables
        )

    # ── Report Dispatcher Helper ─────────────────────────────────────────

    async def _dispatch_report_to_subscribers(
        self,
        template: NotificationTemplate,
        subscribers: List[NotificationSubscriber],
        variables: dict,
    ) -> None:
        """Renders the template and dispatches to every subscriber."""
        from app.modules.hr.hr_models import Employee
        for sub in subscribers:
            try:
                employee = self._repo._session.get(Employee, sub.employee_id)
                if not employee:
                    continue

                contact = (
                    employee.email if sub.channel == "EMAIL"
                    else getattr(employee, "phone", None)
                )
                if not contact:
                    logger.warning(
                        "Subscriber employee_id=%s has no contact for channel %s",
                        sub.employee_id, sub.channel,
                    )
                    continue

                subject_rendered = self._render(template, variables) if template.subject else None
                # Re-render subject cleanly
                if template.subject:
                    subject_rendered = template.subject
                    for key, val in variables.items():
                        subject_rendered = subject_rendered.replace(f"{{{{{key}}}}}", str(val))

                await self._dispatch_internal(
                    template, sub.channel, "EMPLOYEE", sub.employee_id, contact, variables,
                    override_subject=subject_rendered,
                )
            except Exception as e:
                logger.error(
                    "Failed to dispatch report to subscriber employee_id=%s: %s",
                    sub.employee_id, e,
                )

    # ── Private helpers ──────────────────────────────────────────────────

    def _render(self, template: NotificationTemplate, variables: dict) -> str:
        """Simple {{key}} substitution."""
        body = template.body
        for key, val in variables.items():
            body = body.replace(f"{{{{{key}}}}}", str(val))
        return body

    def _resolve_contact_info(
        self, student_id: int
    ) -> Tuple[Optional[str], Optional[int], str, str]:
        """Returns (phone, parent_id, parent_name, student_name)."""
        student = self._repo._session.get(Student, student_id)
        if not student:
            return None, None, "", ""

        stmt = select(Parent, StudentParent).join(StudentParent).where(
            StudentParent.student_id == student_id,
            StudentParent.is_primary == True,
        )
        result = self._repo._session.exec(stmt).first()

        # Fallback to any parent if no primary link exists
        if not result:
            stmt2 = select(Parent, StudentParent).join(StudentParent).where(
                StudentParent.student_id == student_id
            )
            result = self._repo._session.exec(stmt2).first()

        if result:
            parent, _ = result
            return parent.phone_primary, parent.id, parent.full_name, student.full_name

        return None, None, "", student.full_name

    async def _dispatch_internal(
        self,
        template: NotificationTemplate,
        default_channel: str,
        recipient_type: str,
        recipient_id: int,
        contact: str,
        variables: dict,
        override_subject: Optional[str] = None,
    ) -> None:
        channel = template.channel or default_channel
        body = self._render(template, variables)

        if override_subject:
            subject_rendered = override_subject
        elif template.subject:
            subject_rendered = template.subject
            for key, val in variables.items():
                subject_rendered = subject_rendered.replace(f"{{{{{key}}}}}", str(val))
        else:
            subject_rendered = None

        # Write audit log before dispatch
        log = self._repo.create_log(
            template_id=template.id,
            channel=channel,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            recipient_contact=contact,
            body=body,
            subject=subject_rendered,
        )

        # Dispatch
        success, error = False, "Unknown channel"
        if channel == "WHATSAPP":
            success, error = await self._whatsapp.send(contact, body)
        elif channel == "EMAIL":
            success, error = await self._email.send(contact, body, subject_rendered)

        # Update log with outcome
        status = "SENT" if success else "FAILED"
        self._repo.update_log_status(log.id, status, error)
