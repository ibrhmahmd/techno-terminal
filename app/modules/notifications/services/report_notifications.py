"""
app/modules/notifications/services/report_notifications.py
─────────────────────────────────────────────────────────────
Scheduled report notifications for employees.
"""
from datetime import date, timedelta
import logging

from app.modules.notifications.services.base_notification_service import BaseNotificationService
from app.modules.notifications.repositories.notification_repository import NotificationRepository


logger = logging.getLogger(__name__)


class ReportNotificationService(BaseNotificationService):
    """Handles: daily, weekly, monthly business reports."""
    
    def __init__(self, repo: NotificationRepository):
        super().__init__(repo)
    
    # ── Scheduled Report Methods ─────────────────────────────────────────
    
    async def send_daily_report(self) -> None:
        """Daily business summary to all admins."""
        template = self._repo.get_template_by_name("daily_report")
        if not template or not template.is_active:
            logger.warning("daily_report template not found or inactive - skipping.")
            return
        
        # Get notification recipients based on admin settings
        recipients = self._resolve_notification_recipients("daily_report")
        if not recipients:
            logger.info("No recipients enabled for daily report - skipping.")
            return
        
        today = date.today()
        aggregates = self._fetch_daily_aggregates(today)
        
        variables = {
            "date": today.strftime("%Y-%m-%d"),
            "total_revenue": f"{aggregates['total_revenue']:.2f}",
            "new_enrollments": aggregates["new_enrollments"],
            "sessions_held": aggregates["sessions_held"],
            "absent_count": aggregates["absent_count"],
        }
        
        # Send to all enabled recipients (admins + additional recipients)
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)
    
    async def send_weekly_report(self) -> None:
        """Weekly business summary to all admins."""
        template = self._repo.get_template_by_name("weekly_report")
        if not template or not template.is_active:
            logger.warning("weekly_report template not found or inactive - skipping.")
            return
        
        # Get notification recipients based on admin settings
        recipients = self._resolve_notification_recipients("weekly_report")
        if not recipients:
            logger.info("No recipients enabled for weekly report - skipping.")
            return
        
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = today
        
        aggregates = self._fetch_weekly_aggregates(week_start, week_end)
        
        variables = {
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d"),
            "total_revenue": f"{aggregates['total_revenue']:.2f}",
            "new_students": aggregates["new_students"],
            "attendance_rate": f"{aggregates['attendance_rate']:.1f}",
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
        
        # Get notification recipients based on admin settings
        recipients = self._resolve_notification_recipients("monthly_report")
        if not recipients:
            logger.info("No recipients enabled for monthly report - skipping.")
            return
        
        today = date.today()
        month_start = today.replace(day=1)
        
        aggregates = self._fetch_monthly_aggregates(month_start, today)
        
        variables = {
            "month": today.strftime("%B %Y"),
            "total_revenue": f"{aggregates['total_revenue']:.2f}",
            "new_enrollments": aggregates["new_enrollments"],
            "active_students": aggregates["active_students"],
        }
        
        # Send to all enabled recipients (admins + additional recipients)
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)
    
    # ── Private Helpers ──────────────────────────────────────────────────
    
    def _fetch_daily_aggregates(self, target_date: date) -> dict:
        """Fetch daily metrics."""
        total_revenue = 0.0
        new_enrollments = 0
        sessions_held = 0
        absent_count = 0
        
        try:
            from app.modules.analytics.services.financial_service import FinancialAnalyticsService
            fin_svc = FinancialAnalyticsService()
            revenue_data = fin_svc.get_revenue_by_date(target_date, target_date)
            total_revenue = sum(r.net_revenue for r in revenue_data)
        except Exception as e:
            logger.warning(f"Could not fetch daily revenue: {e}")
        
        try:
            from app.modules.analytics.services.academic_service import AcademicAnalyticsService
            academic_svc = AcademicAnalyticsService()
            summary = academic_svc.get_dashboard_summary()
            sessions_held = summary.today_sessions_count
            absent_count = sum(s.absent for s in summary.sessions)
        except Exception as e:
            logger.warning(f"Could not fetch daily academic summary: {e}")
        
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
            logger.warning(f"Could not fetch new enrollments count: {e}")
        
        return {
            "total_revenue": total_revenue,
            "new_enrollments": new_enrollments,
            "sessions_held": sessions_held,
            "absent_count": absent_count,
        }
    
    def _fetch_weekly_aggregates(self, week_start: date, week_end: date) -> dict:
        """Fetch weekly metrics."""
        total_revenue = 0.0
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
        
        return {
            "total_revenue": total_revenue,
            "new_students": new_students,
            "attendance_rate": attendance_rate,
        }
    
    def _fetch_monthly_aggregates(self, month_start: date, month_end: date) -> dict:
        """Fetch monthly metrics."""
        total_revenue = 0.0
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
        
        return {
            "total_revenue": total_revenue,
            "new_enrollments": new_enrollments,
            "active_students": active_students,
        }
    
    # ── Bulk Marketing (now sends to all admins via email) ──────────────
    
    def send_bulk(
        self, parent_ids: list[int], template_name: str, extra_vars: dict,
        background_tasks
    ) -> int:
        """Queue email messages to all admins. Returns queued count."""
        template = self._repo.get_template_by_name(template_name)
        if not template or not template.is_active:
            return 0
        
        # Get notification recipients based on admin settings
        recipients = self._resolve_notification_recipients("bulk")
        if not recipients:
            return 0
        
        count = 0
        for email, recipient_id, recipient_type in recipients:
            variables = extra_vars.copy()
            variables.setdefault("parent_name", "Admin")
            
            background_tasks.add_task(
                self._dispatch, template, "EMAIL", recipient_type,
                recipient_id, email, variables
            )
            count += 1
        
        # PARENT CODE PRESERVED (disabled):
        # from app.modules.crm.models.parent_models import Parent
        # for pid in parent_ids:
        #     parent = self._repo._session.get(Parent, pid)
        #     if not parent or not parent.phone_primary:
        #         continue
        #     variables = extra_vars.copy()
        #     variables.setdefault("parent_name", parent.full_name)
        #     background_tasks.add_task(
        #         self._dispatch, template, "WHATSAPP", "PARENT",
        #         pid, parent.phone_primary, variables
        #     )
        #     count += 1
        
        return count
