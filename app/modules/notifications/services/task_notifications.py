"""
app/modules/notifications/services/task_notifications.py
──────────────────────────────────────────────────────────
Task notification handlers.

Covers:
  - task_assigned          → notify assigned employee
  - task_status_changed    → notify assigned employee + admin recipients
  - task_comment_added     → notify assigned employee (if comment not by them)
  - task_due_reminder      → notify assigned employee when task is overdue / 1-day away
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import BackgroundTasks

from app.modules.notifications.services.base_notification_service import BaseNotificationService
from app.modules.notifications.repositories.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)


class TaskNotificationService(BaseNotificationService):
    """Handles all task-lifecycle email notifications."""

    def __init__(self, repo: NotificationRepository) -> None:
        super().__init__(repo)

    # ── Public API ────────────────────────────────────────────────────────

    def notify_task_assigned(
        self,
        task_id: str,
        employee_id: int,
        assigned_by_user_id: Optional[int],
        background_tasks: BackgroundTasks,
    ) -> None:
        """Notify the employee that a task has been assigned to them."""
        background_tasks.add_task(
            self._process_task_assigned, task_id, employee_id, assigned_by_user_id
        )

    def notify_task_status_changed(
        self,
        task_id: str,
        employee_id: Optional[int],
        old_status: str,
        new_status: str,
        changed_by_user_id: Optional[int],
        background_tasks: BackgroundTasks,
    ) -> None:
        """Notify assigned employee + admin recipients when task status changes."""
        background_tasks.add_task(
            self._process_status_changed,
            task_id, employee_id, old_status, new_status, changed_by_user_id,
        )

    def notify_task_comment_added(
        self,
        task_id: str,
        comment_id: str,
        author_user_id: int,
        background_tasks: BackgroundTasks,
    ) -> None:
        """Notify the assigned employee when a comment is added (by someone else)."""
        background_tasks.add_task(
            self._process_comment_added, task_id, comment_id, author_user_id
        )

    def notify_task_due_reminder(
        self,
        task_id: str,
        employee_id: int,
        days_until_due: int,
        background_tasks: BackgroundTasks,
    ) -> None:
        """Notify the assigned employee that a task is due soon / overdue."""
        background_tasks.add_task(
            self._process_due_reminder, task_id, employee_id, days_until_due
        )

    # ── Private Processors ────────────────────────────────────────────────

    async def _process_task_assigned(
        self,
        task_id: str,
        employee_id: int,
        assigned_by_user_id: Optional[int],
    ) -> None:
        from app.modules.tasks.models.task import Task
        from app.modules.hr.models.employee_models import Employee
        from app.modules.auth.models.auth_models import User
        from app.db.connection import get_session

        template = self._get_template_by_name("task_assigned")
        if not template or not template.is_active:
            logger.warning("Template 'task_assigned' not found or inactive — skipping.")
            return

        with get_session() as session:
            import uuid as _uuid
            task = session.get(Task, _uuid.UUID(task_id))
            if not task:
                logger.error("task_assigned: Task %s not found", task_id)
                return

            employee = session.get(Employee, employee_id)
            if not employee or not employee.email:
                logger.warning("task_assigned: Employee %s missing or no email", employee_id)
                return

            assigned_by_name = "Admin"
            if assigned_by_user_id:
                user = session.get(User, assigned_by_user_id)
                if user:
                    assigned_by_name = user.email  # fallback to email; full_name may not exist

            variables = {
                "employee_name": employee.full_name,
                "task_title": task.title,
                "task_priority": (task.priority or "medium").capitalize(),
                "due_date": task.due_date.strftime("%Y-%m-%d") if task.due_date else "Not set",
                "assigned_by_name": assigned_by_name,
                "task_description": task.description or "—",
            }

        await self._dispatch(
            template=template,
            channel="EMAIL",
            recipient_type="EMPLOYEE",
            recipient_id=employee_id,
            contact=employee.email,
            variables=variables,
        )

    async def _process_status_changed(
        self,
        task_id: str,
        employee_id: Optional[int],
        old_status: str,
        new_status: str,
        changed_by_user_id: Optional[int],
    ) -> None:
        from app.modules.tasks.models.task import Task
        from app.modules.hr.models.employee_models import Employee
        from app.modules.auth.models.auth_models import User
        from app.db.connection import get_session

        template = self._get_template_by_name("task_status_changed")
        if not template or not template.is_active:
            logger.warning("Template 'task_status_changed' not found or inactive — skipping.")
            return

        with get_session() as session:
            import uuid as _uuid
            task = session.get(Task, _uuid.UUID(task_id))
            if not task:
                logger.error("task_status_changed: Task %s not found", task_id)
                return

            employee_name = "Unassigned"
            employee_email: Optional[str] = None
            if employee_id:
                employee = session.get(Employee, employee_id)
                if employee:
                    employee_name = employee.full_name
                    employee_email = employee.email

            changed_by_name = "Admin"
            if changed_by_user_id:
                user = session.get(User, changed_by_user_id)
                if user:
                    changed_by_name = user.email

            variables = {
                "task_title": task.title,
                "employee_name": employee_name,
                "old_status": old_status.replace("_", " ").title(),
                "new_status": new_status.replace("_", " ").title(),
                "changed_by_name": changed_by_name,
                "changed_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            }

        # Send to the assigned employee if available
        if employee_id and employee_email:
            await self._dispatch(
                template=template,
                channel="EMAIL",
                recipient_type="EMPLOYEE",
                recipient_id=employee_id,
                contact=employee_email,
                variables=variables,
            )

        # Also notify admin recipients (task managers)
        admin_recipients = self._resolve_notification_recipients(
            notification_type="task_status_changed",
            entity_id=0,
            entity_description=f"Task: {task_id}",
        )
        for contact, recipient_id, recipient_type in admin_recipients:
            # Avoid double-sending to the employee if they are also an admin recipient
            if recipient_type == "EMPLOYEE" and recipient_id == employee_id:
                continue
            await self._dispatch(
                template=template,
                channel="EMAIL",
                recipient_type=recipient_type,
                recipient_id=recipient_id,
                contact=contact,
                variables=variables,
            )

    async def _process_comment_added(
        self,
        task_id: str,
        comment_id: str,
        author_user_id: int,
    ) -> None:
        from app.modules.tasks.models.task import Task, TaskComment
        from app.modules.hr.models.employee_models import Employee
        from app.modules.auth.models.auth_models import User
        from app.db.connection import get_session

        template = self._get_template_by_name("task_comment_added")
        if not template or not template.is_active:
            logger.warning("Template 'task_comment_added' not found or inactive — skipping.")
            return

        with get_session() as session:
            import uuid as _uuid
            task = session.get(Task, _uuid.UUID(task_id))
            if not task or not task.assigned_to:
                return

            comment = session.get(TaskComment, _uuid.UUID(comment_id))
            if not comment:
                logger.error("task_comment_added: Comment %s not found", comment_id)
                return

            employee = session.get(Employee, task.assigned_to)
            if not employee or not employee.email:
                return

            # Don't notify if the employee themselves commented (matched via user_id)
            # We compare assigned employee's linked user id — skip if same user
            # (best-effort; employee.user_id may be None for older records)
            if getattr(employee, "user_id", None) and employee.user_id == author_user_id:
                return

            author = session.get(User, author_user_id)
            author_name = author.email if author else "Someone"

            variables = {
                "task_title": task.title,
                "employee_name": employee.full_name,
                "author_name": author_name,
                "comment_content": comment.content,
                "commented_at": comment.created_at.strftime("%Y-%m-%d %H:%M UTC"),
            }

        await self._dispatch(
            template=template,
            channel="EMAIL",
            recipient_type="EMPLOYEE",
            recipient_id=task.assigned_to,
            contact=employee.email,
            variables=variables,
        )

    async def _process_due_reminder(
        self,
        task_id: str,
        employee_id: int,
        days_until_due: int,
    ) -> None:
        from app.modules.tasks.models.task import Task
        from app.modules.hr.models.employee_models import Employee
        from app.db.connection import get_session

        template = self._get_template_by_name("task_due_reminder")
        if not template or not template.is_active:
            logger.warning("Template 'task_due_reminder' not found or inactive — skipping.")
            return

        with get_session() as session:
            import uuid as _uuid
            task = session.get(Task, _uuid.UUID(task_id))
            if not task:
                return

            employee = session.get(Employee, employee_id)
            if not employee or not employee.email:
                return

            if days_until_due == 0:
                days_label = "today"
            elif days_until_due < 0:
                days_label = f"{abs(days_until_due)} day(s) ago (overdue)"
            else:
                days_label = f"in {days_until_due} day(s)"

            variables = {
                "employee_name": employee.full_name,
                "task_title": task.title,
                "task_priority": (task.priority or "medium").capitalize(),
                "task_status": (task.status or "todo").replace("_", " ").title(),
                "due_date": task.due_date.strftime("%Y-%m-%d") if task.due_date else "—",
                "days_until_due": days_label,
            }

        await self._dispatch(
            template=template,
            channel="EMAIL",
            recipient_type="EMPLOYEE",
            recipient_id=employee_id,
            contact=employee.email,
            variables=variables,
        )
