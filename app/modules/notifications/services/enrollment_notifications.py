"""
app/modules/notifications/services/enrollment_notifications.py
─────────────────────────────────────────────────────────────
Enrollment notification handlers.
Kept simple: one public method per notification type.
"""
import logging
from datetime import datetime
from typing import Optional
from fastapi import BackgroundTasks

from app.modules.notifications.services.base_notification_service import BaseNotificationService
from app.modules.notifications.repositories.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)


class EnrollmentNotificationService(BaseNotificationService):
    """Handles: enrollment created, completed, dropped, transferred, level progression."""
    
    def __init__(self, repo: NotificationRepository):
        super().__init__(repo)
    
    # ── Public API ────────────────────────────────────────────────────────
    
    def notify_enrollment_created(
        self, student_id: int, enrollment_id: int, group_id: int,
        level_number: int, background_tasks: BackgroundTasks
    ) -> None:
        """New enrollment confirmation."""
        background_tasks.add_task(
            self._process_created, student_id, enrollment_id, group_id, level_number
        )
    
    def notify_enrollment_updated(
        self, student_id: int, enrollment_id: int, group_id: int,
        changes_summary: str, background_tasks: BackgroundTasks,
        performed_by: Optional[int] = None
    ) -> None:
        """Enrollment financial details updated."""
        background_tasks.add_task(
            self._process_updated, student_id, enrollment_id, group_id, changes_summary, performed_by
        )
    
    def notify_enrollment_completed(
        self, student_id: int, enrollment_id: int, group_id: int,
        level_number: int, completion_date: datetime, background_tasks: BackgroundTasks
    ) -> None:
        """Enrollment finished successfully."""
        background_tasks.add_task(
            self._process_completed, student_id, enrollment_id, group_id, 
            level_number, completion_date
        )
    
    def notify_enrollment_dropped(
        self, student_id: int, enrollment_id: int, group_id: int,
        reason: Optional[str], dropped_by: Optional[int], background_tasks: BackgroundTasks
    ) -> None:
        """Student dropped from enrollment."""
        background_tasks.add_task(
            self._process_dropped, student_id, enrollment_id, group_id, reason, dropped_by
        )
    
    def notify_enrollment_transferred(
        self, student_id: int, from_enrollment_id: int, to_enrollment_id: int,
        from_group_id: int, to_group_id: int, transferred_by: Optional[int],
        background_tasks: BackgroundTasks
    ) -> None:
        """Student transferred between groups."""
        background_tasks.add_task(
            self._process_transferred, student_id, from_enrollment_id, to_enrollment_id,
            from_group_id, to_group_id, transferred_by
        )
    
    def notify_level_progression(
        self, student_id: int, old_level: int, new_level: int,
        group_id: int, enrollment_id: int, background_tasks: BackgroundTasks
    ) -> None:
        """Student progressed to next level."""
        background_tasks.add_task(
            self._process_progression, student_id, old_level, new_level, group_id, enrollment_id
        )
    
    # ── Private Processors ─────────────────────────────────────────────────
    
    def _get_admin_info(self, admin_id: Optional[int]) -> dict[str, str]:
        if not admin_id:
            return {"name": "System Action", "email": "system@technofuture.com"}
        try:
            from app.modules.auth.models.auth_models import User
            from app.modules.hr.models.employee_models import Employee
            with self._new_session() as session:
                user = session.get(User, admin_id)
                if user:
                    if user.employee_id:
                        employee = session.get(Employee, user.employee_id)
                        if employee:
                            return {
                                "name": employee.full_name,
                                "email": employee.email or user.username
                            }
                    return {
                        "name": user.username,
                        "email": user.username
                    }
        except Exception as e:
            logger.error(f"Error fetching admin info for ID {admin_id}: {e}")
        return {"name": "Unknown Administrator", "email": "unknown"}
        
    def _get_course_name(self, group_id: int) -> str:
        try:
            from app.modules.academics.models.group_models import Group
            from app.modules.academics.models.course_models import Course
            with self._new_session() as session:
                group = session.get(Group, group_id)
                if group and group.course_id:
                    course = session.get(Course, group.course_id)
                    if course:
                        return course.name
        except Exception:
            pass
        return "Unknown Course"
    
    async def _process_created(self, student_id: int, enrollment_id: int, 
                               group_id: int, level_number: int) -> None:
        from app.modules.academics.models.group_models import Group
        from app.modules.enrollments.models.enrollment_models import Enrollment
        
        template = self._get_template_by_name("enrollment_confirmation")
        if not template or not template.is_active:
            logger.warning("enrollment_confirmation template not found or inactive — skipping")
            return
        
        # Get notification recipients with entity context for fallback alert
        recipients = self._resolve_notification_recipients(
            "enrollment_created",
            entity_id=enrollment_id,
            entity_description=f"Enrollment #{enrollment_id}"
        )
        
        # Fetch group, enrollment and student info
        group_name = self._get_group_name(group_id)
        instructor = self._get_instructor_name(group_id)
        student_name = self._get_student_name(student_id)
        
        # Get schedule info from group
        schedule = "Schedule not available"
        with self._new_session() as session:
            group = session.get(Group, group_id)
            if group and group.default_day:
                start_time = group.default_time_start.strftime("%I:%M %p") if group.default_time_start else "TBD"
                end_time = group.default_time_end.strftime("%I:%M %p") if group.default_time_end else "TBD"
                schedule = f"{group.default_day} {start_time} - {end_time}"

        # Get enrollment date
        enrollment_date = "N/A"
        with self._new_session() as session:
            enrollment = session.get(Enrollment, enrollment_id)
            if enrollment and enrollment.created_at:
                enrollment_date = enrollment.created_at.strftime("%Y-%m-%d")
        
        admin_info = self._get_admin_info(None) # System action

        variables = {
            "parent_name": "Admin",
            "student_name": student_name,
            "group_name": group_name,
            "course_name": self._get_course_name(group_id),
            "level_number": str(level_number),
            "instructor_name": instructor,
            "admin_name": admin_info["name"],
            "admin_email": admin_info["email"],
            "schedule": schedule,
            "enrollment_id": str(enrollment_id),
            "enrollment_date": enrollment_date,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%I:%M %p"),
        }
        
        # Send to all enabled recipients
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)
            
    async def _process_updated(self, student_id: int, enrollment_id: int,
                               group_id: int, changes_summary: str,
                               performed_by: Optional[int] = None) -> None:
        template = self._get_template_by_name("enrollment_updated")
        if not template or not template.is_active:
            logger.warning("enrollment_updated template not found or inactive — skipping")
            return
        
        # Get notification recipients with entity context for fallback alert
        recipients = self._resolve_notification_recipients(
            "enrollment_updated",
            entity_id=enrollment_id,
            entity_description=f"Enrollment #{enrollment_id} Updated"
        )
        
        student_name = self._get_student_name(student_id)
        admin_info = self._get_admin_info(performed_by)
        
        variables = {
            "parent_name": "Admin",
            "student_name": student_name,
            "group_name": self._get_group_name(group_id),
            "course_name": self._get_course_name(group_id),
            "instructor_name": self._get_instructor_name(group_id),
            "admin_name": admin_info["name"],
            "admin_email": admin_info["email"],
            "changes_summary": changes_summary,
            "enrollment_id": str(enrollment_id),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%I:%M %p"),
        }
        
        # Send to all enabled recipients
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)
    
    async def _process_completed(self, student_id: int, enrollment_id: int,
                                  group_id: int, level_number: int, 
                                  completion_date: datetime) -> None:
        template = self._get_template_by_name("enrollment_completed")
        if not template or not template.is_active:
            logger.warning("enrollment_completed template not found or inactive — skipping")
            return
        
        # Get notification recipients with entity context for fallback alert
        recipients = self._resolve_notification_recipients(
            "enrollment_completed",
            entity_id=enrollment_id,
            entity_description=f"Enrollment #{enrollment_id}"
        )
        
        student_name = self._get_student_name(student_id)
        admin_info = self._get_admin_info(None) # System action
        
        variables = {
            "parent_name": "Admin",
            "student_name": student_name,
            "group_name": self._get_group_name(group_id),
            "course_name": self._get_course_name(group_id),
            "instructor_name": self._get_instructor_name(group_id),
            "admin_name": admin_info["name"],
            "admin_email": admin_info["email"],
            "level_number": str(level_number),
            "completion_date": completion_date.strftime("%Y-%m-%d"),
            "enrollment_id": str(enrollment_id),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%I:%M %p"),
        }
        
        # Send to all enabled recipients (admins + additional recipients)
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)
    
    async def _process_dropped(self, student_id: int, enrollment_id: int,
                                group_id: int, reason: Optional[str],
                                dropped_by: Optional[int]) -> None:
        template = self._get_template_by_name("enrollment_dropped")
        if not template or not template.is_active:
            logger.warning("enrollment_dropped template not found or inactive — skipping")
            return
        
        # Get notification recipients with entity context for fallback alert
        recipients = self._resolve_notification_recipients(
            "enrollment_dropped",
            entity_id=enrollment_id,
            entity_description=f"Enrollment #{enrollment_id}"
        )
        
        student_name = self._get_student_name(student_id)
        admin_info = self._get_admin_info(dropped_by)
        
        variables = {
            "parent_name": "Admin",
            "student_name": student_name,
            "group_name": self._get_group_name(group_id),
            "course_name": self._get_course_name(group_id),
            "instructor_name": self._get_instructor_name(group_id),
            "admin_name": admin_info["name"],
            "admin_email": admin_info["email"],
            "reason": reason or "No reason provided",
            "enrollment_id": str(enrollment_id),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%I:%M %p"),
        }
        
        # Send to all enabled recipients
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)
    
    async def _process_transferred(self, student_id: int, from_enrollment_id: int,
                                    to_enrollment_id: int, from_group_id: int,
                                    to_group_id: int, transferred_by: Optional[int]) -> None:
        template = self._get_template_by_name("enrollment_transferred")
        if not template or not template.is_active:
            logger.warning("enrollment_transferred template not found or inactive — skipping")
            return
        
        # Get notification recipients with entity context for fallback alert
        recipients = self._resolve_notification_recipients(
            "enrollment_transferred",
            entity_id=from_enrollment_id,
            entity_description=f"Transfer from Enrollment #{from_enrollment_id} to #{to_enrollment_id}"
        )
        
        student_name = self._get_student_name(student_id)
        admin_info = self._get_admin_info(transferred_by)
        
        variables = {
            "parent_name": "Admin",
            "student_name": student_name,
            "from_group_name": self._get_group_name(from_group_id),
            "to_group_name": self._get_group_name(to_group_id),
            "course_name": self._get_course_name(to_group_id),
            "instructor_name": self._get_instructor_name(to_group_id),
            "admin_name": admin_info["name"],
            "admin_email": admin_info["email"],
            "from_enrollment_id": str(from_enrollment_id),
            "to_enrollment_id": str(to_enrollment_id),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%I:%M %p"),
        }
        
        # Send to all enabled recipients
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)
    
    async def _process_progression(self, student_id: int, old_level: int,
                                    new_level: int, group_id: int, enrollment_id: int) -> None:
        template = self._get_template_by_name("level_progression")
        if not template or not template.is_active:
            logger.warning("level_progression template not found or inactive — skipping")
            return
        
        # Get notification recipients with entity context for fallback alert
        recipients = self._resolve_notification_recipients(
            "level_progression",
            entity_id=enrollment_id,
            entity_description=f"Enrollment #{enrollment_id} Level {old_level} -> {new_level}"
        )
        
        student_name = self._get_student_name(student_id)
        admin_info = self._get_admin_info(None) # System action
        
        variables = {
            "parent_name": "Admin",
            "student_name": student_name,
            "old_level": str(old_level),
            "new_level": str(new_level),
            "group_name": self._get_group_name(group_id),
            "course_name": self._get_course_name(group_id),
            "instructor_name": self._get_instructor_name(group_id),
            "admin_name": admin_info["name"],
            "admin_email": admin_info["email"],
            "enrollment_id": str(enrollment_id),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%I:%M %p"),
        }
        
        # Send to all enabled recipients
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)
    
    # ── Helpers ───────────────────────────────────────────────────────────
    # Inherited from BaseNotificationService:
    #   _get_group_name(), _get_instructor_name(), _get_student_name()
