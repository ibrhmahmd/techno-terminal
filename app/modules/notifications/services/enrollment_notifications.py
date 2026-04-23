"""
app/modules/notifications/services/enrollment_notifications.py
─────────────────────────────────────────────────────────────
Enrollment notification handlers.
Kept simple: one public method per notification type.
"""
from datetime import datetime
from typing import Optional
from fastapi import BackgroundTasks

from app.modules.notifications.services.base_notification_service import BaseNotificationService
from app.modules.notifications.repositories.notification_repository import NotificationRepository


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
    
    async def _process_created(self, student_id: int, enrollment_id: int, 
                               group_id: int, level_number: int) -> None:
        from app.modules.academics.models.group_models import Group
        from app.modules.enrollments.models.enrollment_models import Enrollment
        
        template = self._repo.get_template_by_name("enrollment_confirmation")
        if not template or not template.is_active:
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
        group = self._repo._session.get(Group, group_id)
        if group and group.default_day:
            from datetime import time as dt_time
            start_time = group.default_time_start.strftime("%I:%M %p") if group.default_time_start else "TBD"
            end_time = group.default_time_end.strftime("%I:%M %p") if group.default_time_end else "TBD"
            schedule = f"{group.default_day} {start_time} - {end_time}"
        
        # Get enrollment date
        enrollment_date = "N/A"
        enrollment = self._repo._session.get(Enrollment, enrollment_id)
        if enrollment and enrollment.created_at:
            enrollment_date = enrollment.created_at.strftime("%Y-%m-%d")
        
        variables = {
            "parent_name": "Admin",
            "student_name": student_name,
            "group_name": group_name,
            "level_number": str(level_number),
            "instructor": instructor,
            "schedule": schedule,
            "enrollment_id": str(enrollment_id),
            "enrollment_date": enrollment_date,
        }
        
        # Send to all enabled recipients
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)
        
        # PARENT CODE PRESERVED (disabled):
        # email, parent_id, parent_name, student_name = self._resolve_contact(
        #     student_id, template.channel
        # )
        # if email and parent_id:
        #     await self._dispatch(template, template.channel, "PARENT", parent_id, email, variables)
    
    async def _process_completed(self, student_id: int, enrollment_id: int,
                                  group_id: int, level_number: int, 
                                  completion_date: datetime) -> None:
        template = self._repo.get_template_by_name("enrollment_completed")
        if not template or not template.is_active:
            return
        
        # Get notification recipients with entity context for fallback alert
        recipients = self._resolve_notification_recipients(
            "enrollment_completed",
            entity_id=enrollment_id,
            entity_description=f"Enrollment #{enrollment_id}"
        )
        
        student_name = self._get_student_name(student_id)
        
        variables = {
            "parent_name": "Admin",
            "student_name": student_name,
            "group_name": self._get_group_name(group_id),
            "level_number": str(level_number),
            "completion_date": completion_date.strftime("%Y-%m-%d"),
            "enrollment_id": str(enrollment_id),
        }
        
        # Send to all enabled recipients (admins + additional recipients)
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)
    
    async def _process_dropped(self, student_id: int, enrollment_id: int,
                                group_id: int, reason: Optional[str],
                                dropped_by: Optional[int]) -> None:
        template = self._repo.get_template_by_name("enrollment_dropped")
        if not template or not template.is_active:
            return
        
        # Get notification recipients with entity context for fallback alert
        recipients = self._resolve_notification_recipients(
            "enrollment_dropped",
            entity_id=enrollment_id,
            entity_description=f"Enrollment #{enrollment_id}"
        )
        
        student_name = self._get_student_name(student_id)
        
        variables = {
            "parent_name": "Admin",
            "student_name": student_name,
            "group_name": self._get_group_name(group_id),
            "reason": reason or "No reason provided",
            "enrollment_id": str(enrollment_id),
        }
        
        # Send to all enabled recipients
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)
        
        # PARENT CODE PRESERVED (disabled):
        # email, parent_id, parent_name, student_name = self._resolve_contact(
        #     student_id, template.channel
        # )
        # if email and parent_id:
        #     await self._dispatch(template, template.channel, "PARENT", parent_id, email, variables)
    
    async def _process_transferred(self, student_id: int, from_enrollment_id: int,
                                    to_enrollment_id: int, from_group_id: int,
                                    to_group_id: int, transferred_by: Optional[int]) -> None:
        template = self._repo.get_template_by_name("enrollment_transferred")
        if not template or not template.is_active:
            return
        
        # Get notification recipients with entity context for fallback alert
        recipients = self._resolve_notification_recipients(
            "enrollment_transferred",
            entity_id=from_enrollment_id,
            entity_description=f"Transfer from Enrollment #{from_enrollment_id} to #{to_enrollment_id}"
        )
        
        student_name = self._get_student_name(student_id)
        
        variables = {
            "parent_name": "Admin",
            "student_name": student_name,
            "from_group_name": self._get_group_name(from_group_id),
            "to_group_name": self._get_group_name(to_group_id),
            "from_enrollment_id": str(from_enrollment_id),
            "to_enrollment_id": str(to_enrollment_id),
        }
        
        # Send to all enabled recipients
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)
        
        # PARENT CODE PRESERVED (disabled):
        # email, parent_id, parent_name, student_name = self._resolve_contact(
        #     student_id, template.channel
        # )
        # if email and parent_id:
        #     await self._dispatch(template, template.channel, "PARENT", parent_id, email, variables)
    
    async def _process_progression(self, student_id: int, old_level: int,
                                    new_level: int, group_id: int, enrollment_id: int) -> None:
        template = self._repo.get_template_by_name("level_progression")
        if not template or not template.is_active:
            return
        
        # Get notification recipients with entity context for fallback alert
        recipients = self._resolve_notification_recipients(
            "level_progression",
            entity_id=enrollment_id,
            entity_description=f"Enrollment #{enrollment_id} Level {old_level} -> {new_level}"
        )
        
        student_name = self._get_student_name(student_id)
        
        variables = {
            "parent_name": "Admin",
            "student_name": student_name,
            "old_level": str(old_level),
            "new_level": str(new_level),
            "group_name": self._get_group_name(group_id),
            "enrollment_id": str(enrollment_id),
        }
        
        # Send to all enabled recipients
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)
        
        # PARENT CODE PRESERVED (disabled):
        # email, parent_id, parent_name, student_name = self._resolve_contact(
        #     student_id, template.channel
        # )
        # if email and parent_id:
        #     await self._dispatch(template, template.channel, "PARENT", parent_id, email, variables)
    
    # ── Helpers ───────────────────────────────────────────────────────────
    
    def _get_group_name(self, group_id: int) -> str:
        from app.modules.academics.models import Group
        group = self._repo._session.get(Group, group_id)
        return group.name if group else "Unknown Group"
    
    def _get_instructor_name(self, group_id: int) -> str:
        from app.modules.academics.models import Group
        from app.modules.hr.models import Employee
        group = self._repo._session.get(Group, group_id)
        if group and group.instructor_id:
            instructor = self._repo._session.get(Employee, group.instructor_id)
            return instructor.full_name if instructor else "Unknown"
        return "Unknown"
    
    def _get_student_name(self, student_id: int) -> str:
        from app.modules.crm.models.student_models import Student
        student = self._repo._session.get(Student, student_id)
        return student.full_name if student else f"Student #{student_id}"
