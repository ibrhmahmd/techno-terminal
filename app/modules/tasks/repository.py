"""Task Repository

Data access for task tracking entities.
Coordinates tasks, subtasks, comments, and time logs.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import aliased
from sqlmodel import Session

from app.modules.tasks.models import Task, TaskSubtask, TaskComment, TaskTimeLog, TaskStatus, TaskPriority
from app.modules.tasks.schemas import (
    CreateTaskInput,
    UpdateTaskInput,
    CreateTaskSubtaskInput,
    UpdateTaskSubtaskInput,
    CreateTaskCommentInput,
    CreateTaskTimeLogInput,
    TaskReadDTO,
    TaskDetailDTO,
    TaskSubtaskReadDTO,
    TaskCommentReadDTO,
    TaskTimeLogReadDTO,
)
from app.modules.hr.models.employee_models import Employee
from app.modules.auth.models.auth_models import User
from app.shared.datetime_utils import utc_now


class TaskRepository:
    """Repository for Task and related models."""

    def __init__(self, session: Session):
        self._session = session

    def create_task(self, dto: CreateTaskInput, assigned_by_user_id: int) -> Task:
        """Create a new task."""
        task_data = dto.model_dump(exclude_unset=True)
        task = Task(
            **task_data,
            assigned_by=assigned_by_user_id,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        self._session.add(task)
        self._session.flush()
        return task

    def update_task(self, task_id: uuid.UUID, dto: UpdateTaskInput, deleted_by_user_id: Optional[int] = None) -> Optional[Task]:
        """Update a task."""
        task = self._session.get(Task, task_id)
        if not task or (task.deleted_at is not None and not deleted_by_user_id):
            return None

        update_data = dto.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)

        task.updated_at = utc_now()
        self._session.add(task)
        self._session.flush()
        return task

    def get_task_by_id(self, task_id: uuid.UUID) -> Optional[Task]:
        """Get raw task model by ID (active only)."""
        task = self._session.get(Task, task_id)
        if task and task.deleted_at is None:
            return task
        return None

    def get_task_dto(self, task_id: uuid.UUID) -> Optional[TaskDetailDTO]:
        """Get detailed task DTO with relations."""
        task = self.get_task_by_id(task_id)
        if not task:
            return None

        # Resolve names
        assignee_name = None
        if task.assigned_to:
            emp = self._session.get(Employee, task.assigned_to)
            if emp:
                assignee_name = emp.full_name

        assignor_name = None
        if task.assigned_by:
            usr = self._session.get(User, task.assigned_by)
            if usr:
                if usr.employee_id:
                    emp = self._session.get(Employee, usr.employee_id)
                    assignor_name = emp.full_name if emp else usr.username
                else:
                    assignor_name = usr.username

        # Get subtasks
        subtasks_stmt = select(TaskSubtask).where(TaskSubtask.task_id == task_id).order_by(TaskSubtask.created_at.asc())
        subtasks_models = self._session.exec(subtasks_stmt).all()
        subtasks = [TaskSubtaskReadDTO.model_validate(s) for s in subtasks_models]

        # Get comments with author names
        CommentAuthorUser = aliased(User)
        CommentAuthorEmployee = aliased(Employee)
        comments_stmt = (
            select(TaskComment, CommentAuthorUser.username, CommentAuthorEmployee.full_name)
            .where(TaskComment.task_id == task_id)
            .outerjoin(CommentAuthorUser, TaskComment.author_id == CommentAuthorUser.id)
            .outerjoin(CommentAuthorEmployee, CommentAuthorUser.employee_id == CommentAuthorEmployee.id)
            .order_by(TaskComment.created_at.asc())
        )
        comments_results = self._session.exec(comments_stmt).all()
        comments = []
        for comment, username, emp_name in comments_results:
            comments.append(
                TaskCommentReadDTO(
                    id=comment.id,
                    task_id=comment.task_id,
                    author_id=comment.author_id,
                    author_name=emp_name or username or "System Admin",
                    content=comment.content,
                    created_at=comment.created_at,
                    updated_at=comment.updated_at,
                )
            )

        # Get time logs with employee names
        TimeLogEmployee = aliased(Employee)
        timelogs_stmt = (
            select(TaskTimeLog, TimeLogEmployee.full_name)
            .where(TaskTimeLog.task_id == task_id)
            .outerjoin(TimeLogEmployee, TaskTimeLog.employee_id == TimeLogEmployee.id)
            .order_by(TaskTimeLog.logged_at.desc())
        )
        timelogs_results = self._session.exec(timelogs_stmt).all()
        time_logs = []
        for log, emp_name in timelogs_results:
            time_logs.append(
                TaskTimeLogReadDTO(
                    id=log.id,
                    task_id=log.task_id,
                    employee_id=log.employee_id,
                    employee_name=emp_name or f"Employee #{log.employee_id}",
                    hours=log.hours,
                    note=log.note,
                    logged_at=log.logged_at,
                    created_at=log.created_at,
                )
            )

        return TaskDetailDTO(
            id=task.id,
            title=task.title,
            description=task.description,
            due_date=task.due_date,
            priority=task.priority,
            status=task.status,
            assigned_to=task.assigned_to,
            assigned_to_name=assignee_name,
            assigned_by=task.assigned_by,
            assigned_by_name=assignor_name,
            estimated_hours=task.estimated_hours,
            tags=task.tags,
            is_recurring=task.is_recurring,
            recurrence_pattern=task.recurrence_pattern,
            parent_task_id=task.parent_task_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
            subtasks=subtasks,
            comments=comments,
            time_logs=time_logs,
        )

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assigned_to: Optional[int] = None,
        is_recurring: Optional[bool] = None,
        include_deleted: bool = False,
    ) -> list[TaskReadDTO]:
        """List tasks with optional filters."""
        AssigneeEmployee = aliased(Employee)
        AssignorUser = aliased(User)
        AssignorEmployee = aliased(Employee)

        stmt = (
            select(Task, AssigneeEmployee.full_name, AssignorUser.username, AssignorEmployee.full_name)
            .outerjoin(AssigneeEmployee, Task.assigned_to == AssigneeEmployee.id)
            .outerjoin(AssignorUser, Task.assigned_by == AssignorUser.id)
            .outerjoin(AssignorEmployee, AssignorUser.employee_id == AssignorEmployee.id)
        )

        conditions = []
        if not include_deleted:
            conditions.append(Task.deleted_at == None)
        if status:
            conditions.append(Task.status == status)
        if priority:
            conditions.append(Task.priority == priority)
        if assigned_to:
            conditions.append(Task.assigned_to == assigned_to)
        if is_recurring is not None:
            conditions.append(Task.is_recurring == is_recurring)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(Task.due_date.asc(), Task.created_at.desc())
        results = self._session.exec(stmt).all()

        return [
            TaskReadDTO(
                id=task.id,
                title=task.title,
                description=task.description,
                due_date=task.due_date,
                priority=task.priority,
                status=task.status,
                assigned_to=task.assigned_to,
                assigned_to_name=assignee_name,
                assigned_by=task.assigned_by,
                assigned_by_name=assignor_emp_name or assignor_username or "System Admin",
                estimated_hours=task.estimated_hours,
                tags=task.tags,
                is_recurring=task.is_recurring,
                recurrence_pattern=task.recurrence_pattern,
                parent_task_id=task.parent_task_id,
                created_at=task.created_at,
                updated_at=task.updated_at,
            )
            for task, assignee_name, assignor_username, assignor_emp_name in results
        ]

    def soft_delete(self, task_id: uuid.UUID, deleted_by_user_id: int) -> bool:
        """Soft delete a task."""
        task = self._session.get(Task, task_id)
        if not task or task.deleted_at is not None:
            return False

        task.deleted_at = utc_now()
        task.deleted_by = deleted_by_user_id
        task.updated_at = utc_now()
        self._session.add(task)
        self._session.flush()
        return True

    # --- Subtask Methods ---
    def create_subtask(self, task_id: uuid.UUID, dto: CreateTaskSubtaskInput) -> TaskSubtask:
        """Create a subtask."""
        subtask = TaskSubtask(
            task_id=task_id,
            title=dto.title,
            is_done=False,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        self._session.add(subtask)
        self._session.flush()
        return subtask

    def update_subtask(self, subtask_id: uuid.UUID, dto: UpdateTaskSubtaskInput) -> Optional[TaskSubtask]:
        """Update a subtask."""
        subtask = self._session.get(TaskSubtask, subtask_id)
        if not subtask:
            return None

        update_data = dto.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(subtask, key, value)

        subtask.updated_at = utc_now()
        self._session.add(subtask)
        self._session.flush()
        return subtask

    def get_subtask_by_id(self, subtask_id: uuid.UUID) -> Optional[TaskSubtask]:
        """Get a subtask by ID."""
        return self._session.get(TaskSubtask, subtask_id)

    def delete_subtask(self, subtask_id: uuid.UUID) -> bool:
        """Delete a subtask."""
        subtask = self._session.get(TaskSubtask, subtask_id)
        if not subtask:
            return False
        self._session.delete(subtask)
        self._session.flush()
        return True

    # --- Comment Methods ---
    def create_comment(self, task_id: uuid.UUID, author_id: int, dto: CreateTaskCommentInput) -> TaskComment:
        """Create a comment."""
        comment = TaskComment(
            task_id=task_id,
            author_id=author_id,
            content=dto.content,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        self._session.add(comment)
        self._session.flush()
        return comment

    def get_comment_by_id(self, comment_id: uuid.UUID) -> Optional[TaskComment]:
        """Get a comment by ID."""
        return self._session.get(TaskComment, comment_id)

    def delete_comment(self, comment_id: uuid.UUID) -> bool:
        """Delete a comment."""
        comment = self._session.get(TaskComment, comment_id)
        if not comment:
            return False
        self._session.delete(comment)
        self._session.flush()
        return True

    # --- Time Log Methods ---
    def create_time_log(self, task_id: uuid.UUID, employee_id: int, dto: CreateTaskTimeLogInput) -> TaskTimeLog:
        """Create a time log."""
        log = TaskTimeLog(
            task_id=task_id,
            employee_id=employee_id,
            hours=dto.hours,
            note=dto.note,
            logged_at=utc_now(),
            created_at=utc_now(),
        )
        self._session.add(log)
        self._session.flush()
        return log

    def get_time_log_by_id(self, log_id: uuid.UUID) -> Optional[TaskTimeLog]:
        """Get a time log by ID."""
        return self._session.get(TaskTimeLog, log_id)


class TasksUnitOfWork:
    """Unit of Work for Tasks module transactions."""

    def __init__(self, session: Session):
        self._session = session
        self.tasks = TaskRepository(session)

    def commit(self) -> None:
        """Commit the transaction."""
        self._session.commit()

    def flush(self) -> None:
        """Flush pending changes."""
        self._session.flush()

    def rollback(self) -> None:
        """Rollback transaction."""
        self._session.rollback()
