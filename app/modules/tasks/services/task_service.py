"""Task Service

Business logic and access control rules for tasks.
"""
import logging
import uuid
from datetime import date
from typing import Optional

from app.modules.tasks.models import Task, TaskSubtask, TaskComment, TaskTimeLog, TaskStatus, TaskPriority
from app.db.uow import UnitOfWork
from app.modules.tasks.ports import TaskNotifier
from app.modules.tasks.repositories.task_repository import TaskRepository
from app.modules.tasks.schemas.task_schemas import (
    CreateTaskInput,
    UpdateTaskInput,
    CreateTaskSubtaskInput,
    UpdateTaskSubtaskInput,
    CreateTaskCommentInput,
    CreateTaskTimeLogInput,
    TaskReadDTO,
    TaskDetailDTO,
)
from app.modules.auth.models.auth_models import User
from app.modules.hr.models.employee_models import Employee
from app.shared.exceptions import AuthError, NotFoundError
from app.shared.datetime_utils import cairo_day_bounds, utc_now
from sqlmodel import select
from datetime import timedelta
from app.modules.tasks.models import Task, TaskSubtask
logger = logging.getLogger(__name__)


class TaskService:
    """Service handling task business rules and transactions."""

    def __init__(
        self,
        uow: UnitOfWork,
        notifier: Optional[TaskNotifier] = None,
    ):
        self._uow = uow
        self._notifier = notifier
        self._tasks = TaskRepository(uow.session)

    def _notify(self, method: str, **kwargs) -> None:
        """Call the notifier after commit; failures are logged, never raised."""
        if self._notifier is None:
            return
        try:
            getattr(self._notifier, method)(**kwargs)
        except Exception:
            logger.exception("Task notifier %s failed", method)

    def _is_admin(self, user: User) -> bool:
        return user.role in ("admin", "system_admin")

    def create_task(
        self,
        dto: CreateTaskInput,
        current_user: User,
    ) -> TaskDetailDTO:
        """Create a new task (Admin only)."""
        if not self._is_admin(current_user):
            raise AuthError("Only admins can create tasks.")

        # If assigned_to is provided, verify employee exists
        if dto.assigned_to:
            # We can perform a quick session look up on Employee
            emp = self._uow._session.get(Employee, dto.assigned_to) if 'Employee' in globals() else self._uow._session.execute(
                select(Employee).where(Employee.id == dto.assigned_to)
            ).scalar_one_or_none()
            if not emp:
                raise NotFoundError(f"Employee {dto.assigned_to} not found.")

        task = self._tasks.create_task(dto, current_user.id)
        self._uow.flush()
        
        # Build initial subtasks if any were passed (none in basic Task creation, but good to have)
        self._uow.commit()

        detail = self._tasks.get_task_dto(task.id)
        if not detail:
            raise NotFoundError("Failed to fetch created task details.")

        # Trigger assigned notification if employee was set
        if dto.assigned_to:
            self._notify(
                "task_assigned",
                task_id=task.id,
                employee_id=dto.assigned_to,
                assigned_by_user_id=current_user.id,
            )

        return detail

    def update_task(
        self,
        task_id: uuid.UUID,
        dto: UpdateTaskInput,
        current_user: User,
    ) -> TaskDetailDTO:
        """Update a task with role-based checks."""
        task = self._tasks.get_task_by_id(task_id)
        if not task:
            raise NotFoundError(f"Task {task_id} not found.")

        old_status = task.status
        is_admin = self._is_admin(current_user)

        if not is_admin:
            # Employee check
            if current_user.employee_id is None or task.assigned_to != current_user.employee_id:
                raise AuthError("You can only update tasks assigned to you.")

            # Employees can ONLY update status
            update_fields = dto.model_dump(exclude_unset=True)
            non_status_fields = [k for k in update_fields.keys() if k != "status"]
            if non_status_fields:
                raise AuthError("Employees can only update task status.")

        # Perform the update
        self._tasks.update_task(task_id, dto)
        self._uow.flush()
        self._uow.commit()

        detail = self._tasks.get_task_dto(task_id)
        if not detail:
            raise NotFoundError(f"Task {task_id} not found after update.")

        # Trigger status-change notification
        new_status = dto.model_dump(exclude_unset=True).get("status")
        if new_status is not None and new_status != old_status:
            self._notify(
                "task_status_changed",
                task_id=task_id,
                employee_id=task.assigned_to,
                old_status=old_status,
                new_status=new_status,
                changed_by_user_id=current_user.id,
            )

        return detail

    def get_task(self, task_id: uuid.UUID, current_user: User) -> TaskDetailDTO:
        """Get task detail by ID (Colleague read-only allowed)."""
        detail = self._tasks.get_task_dto(task_id)
        if not detail:
            raise NotFoundError(f"Task {task_id} not found.")
        return detail

    def list_tasks(
        self,
        current_user: User,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assigned_to: Optional[int] = None,
        is_recurring: Optional[bool] = None,
    ) -> list[TaskReadDTO]:
        """List tasks with optional filters."""
        return self._tasks.list_tasks(
            status=status,
            priority=priority,
            assigned_to=assigned_to,
            is_recurring=is_recurring,
        )

    def soft_delete(self, task_id: uuid.UUID, current_user: User) -> None:
        """Soft delete a task (Admin only)."""
        if not self._is_admin(current_user):
            raise AuthError("Only admins can delete tasks.")

        task = self._tasks.get_task_by_id(task_id)
        if not task:
            raise NotFoundError(f"Task {task_id} not found.")

        self._tasks.soft_delete(task_id, current_user.id)
        self._uow.commit()

    # --- Subtask Methods ---
    def add_subtask(self, task_id: uuid.UUID, dto: CreateTaskSubtaskInput, current_user: User) -> TaskSubtask:
        """Add subtask (Admin only)."""
        if not self._is_admin(current_user):
            raise AuthError("Only admins can add subtasks.")

        task = self._tasks.get_task_by_id(task_id)
        if not task:
            raise NotFoundError(f"Task {task_id} not found.")

        subtask = self._tasks.create_subtask(task_id, dto)
        self._uow.commit()
        return subtask

    def update_subtask(self, subtask_id: uuid.UUID, dto: UpdateTaskSubtaskInput, current_user: User) -> TaskSubtask:
        """Update subtask (Admin or assigned employee)."""
        subtask = self._tasks.get_subtask_by_id(subtask_id)
        if not subtask:
            raise NotFoundError(f"Subtask {subtask_id} not found.")

        task = self._tasks.get_task_by_id(subtask.task_id)
        if not task:
            raise NotFoundError("Associated task not found.")

        is_admin = self._is_admin(current_user)
        if not is_admin:
            # Employee check
            if current_user.employee_id is None or task.assigned_to != current_user.employee_id:
                raise AuthError("You can only update subtasks on tasks assigned to you.")
            
            # Employee can only modify 'is_done'
            update_fields = dto.model_dump(exclude_unset=True)
            non_done_fields = [k for k in update_fields.keys() if k != "is_done"]
            if non_done_fields:
                raise AuthError("Employees can only toggle subtask completion status.")

        updated = self._tasks.update_subtask(subtask_id, dto)
        if not updated:
            raise NotFoundError("Failed to update subtask.")
        self._uow.commit()
        return updated

    def delete_subtask(self, subtask_id: uuid.UUID, current_user: User) -> None:
        """Delete subtask (Admin only)."""
        if not self._is_admin(current_user):
            raise AuthError("Only admins can delete subtasks.")

        subtask = self._tasks.get_subtask_by_id(subtask_id)
        if not subtask:
            raise NotFoundError(f"Subtask {subtask_id} not found.")

        self._tasks.delete_subtask(subtask_id)
        self._uow.commit()

    # --- Comment Methods ---
    def add_comment(
        self,
        task_id: uuid.UUID,
        dto: CreateTaskCommentInput,
        current_user: User,
    ) -> TaskComment:
        """Add a comment (Admin or assigned employee)."""
        task = self._tasks.get_task_by_id(task_id)
        if not task:
            raise NotFoundError(f"Task {task_id} not found.")

        is_admin = self._is_admin(current_user)
        if not is_admin:
            if current_user.employee_id is None or task.assigned_to != current_user.employee_id:
                raise AuthError("You can only comment on tasks assigned to you.")

        comment = self._tasks.create_comment(task_id, current_user.id, dto)
        self._uow.commit()

        # Notify assigned employee when someone else comments
        if task.assigned_to is not None:
            self._notify(
                "task_comment_added",
                task_id=task_id,
                comment_id=comment.id,
                author_user_id=current_user.id,
            )

        return comment

    def delete_comment(self, comment_id: uuid.UUID, current_user: User) -> None:
        """Delete comment (Author or admin only)."""
        comment = self._tasks.get_comment_by_id(comment_id)
        if not comment:
            raise NotFoundError(f"Comment {comment_id} not found.")

        is_admin = self._is_admin(current_user)
        if not is_admin and comment.author_id != current_user.id:
            raise AuthError("You can only delete your own comments.")

        self._tasks.delete_comment(comment_id)
        self._uow.commit()

    # --- Time Log Methods ---
    def add_time_log(self, task_id: uuid.UUID, dto: CreateTaskTimeLogInput, current_user: User) -> TaskTimeLog:
        """Add time log (Assigned employee only)."""
        task = self._tasks.get_task_by_id(task_id)
        if not task:
            raise NotFoundError(f"Task {task_id} not found.")

        if current_user.employee_id is None or task.assigned_to != current_user.employee_id:
            raise AuthError("You can only log time on tasks assigned to you.")

        log = self._tasks.create_time_log(task_id, current_user.employee_id, dto)
        self._uow.commit()
        return log

    def spawn_recurring_tasks(self, target_date: date) -> int:
        """Spawn child tasks from active recurring task templates for target_date."""
        
        # 1. Fetch all active templates
        stmt = select(Task).where(Task.is_recurring == True, Task.deleted_at == None)
        templates = self._uow._session.exec(stmt).all()
        
        spawned_count = 0
        
        for parent in templates:
            should_spawn = False
            
            # Check recurrence pattern
            if parent.recurrence_pattern == "daily":
                should_spawn = True
            elif parent.recurrence_pattern == "weekly":
                if parent.recurrence_day_of_week is not None:
                    # target_date.weekday() is 0 (Monday) to 6 (Sunday)
                    if target_date.weekday() == parent.recurrence_day_of_week:
                        should_spawn = True
            elif parent.recurrence_pattern == "monthly":
                if parent.recurrence_day_of_month is not None:
                    if target_date.day == parent.recurrence_day_of_month:
                        should_spawn = True
            elif parent.recurrence_pattern == "custom_interval":
                if parent.recurrence_interval_days:
                    # Get latest child task created
                    latest_child_stmt = (
                        select(Task)
                        .where(Task.parent_task_id == parent.id)
                        .order_by(Task.created_at.desc())
                        .limit(1)
                    )
                    latest_child = self._uow._session.exec(latest_child_stmt).first()
                    
                    base_date = latest_child.created_at.date() if latest_child else parent.created_at.date()
                    if (target_date - base_date).days >= parent.recurrence_interval_days:
                        should_spawn = True
                        
            if not should_spawn:
                continue
                
            # Prevent double spawning
            start_dt, end_dt = cairo_day_bounds(target_date)
            
            check_stmt = select(Task).where(
                Task.parent_task_id == parent.id,
                Task.created_at >= start_dt,
                Task.created_at < end_dt
            )
            already_spawned = self._uow._session.exec(check_stmt).first()
            if already_spawned:
                continue
                
            # Create child task
            now = utc_now()
            child_created = now if start_dt <= now < end_dt else start_dt
            child = Task(
                title=parent.title,
                description=parent.description,
                priority=parent.priority,
                status="todo",
                assigned_to=parent.assigned_to,
                assigned_by=parent.assigned_by,
                estimated_hours=parent.estimated_hours,
                tags=parent.tags,
                is_recurring=False,
                parent_task_id=parent.id,
                created_at=child_created,
                updated_at=child_created
            )
            
            # Calculate due date
            if parent.due_date:
                parent_offset = (parent.due_date - parent.created_at.date()).days
                child.due_date = target_date + timedelta(days=max(0, parent_offset))
            else:
                child.due_date = None
                
            self._uow._session.add(child)
            self._uow.flush() # gets child.id
            
            # Clone subtasks
            subtasks_stmt = select(TaskSubtask).where(TaskSubtask.task_id == parent.id)
            parent_subtasks = self._uow._session.exec(subtasks_stmt).all()
            for sub in parent_subtasks:
                child_sub = TaskSubtask(
                    task_id=child.id,
                    title=sub.title,
                    is_done=False,
                    created_at=utc_now(),
                    updated_at=utc_now()
                )
                self._uow._session.add(child_sub)
                
            spawned_count += 1
            
        if spawned_count > 0:
            self._uow.commit()
            
        return spawned_count


