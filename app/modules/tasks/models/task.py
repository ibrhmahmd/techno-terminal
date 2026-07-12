"""Task Models

SQLModel entities for employee tasks tracking.
"""
import uuid
from datetime import date, datetime, timezone
from typing import Optional, Literal, TypeAlias
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import SQLModel, Field

# Types for task constraints/enums
TaskStatus: TypeAlias = Literal["todo", "in_progress", "done", "cancelled", "overdue"]
TaskPriority: TypeAlias = Literal["low", "medium", "high", "urgent"]
TaskRecurrencePattern: TypeAlias = Literal["daily", "weekly", "monthly", "custom_interval"]

TASK_STATUSES: list[TaskStatus] = ["todo", "in_progress", "done", "cancelled", "overdue"]
TASK_PRIORITIES: list[TaskPriority] = ["low", "medium", "high", "urgent"]
TASK_RECURRENCE_PATTERNS: list[TaskRecurrencePattern] = ["daily", "weekly", "monthly", "custom_interval"]


class Task(SQLModel, table=True):
    """Task database model."""
    __tablename__ = "tasks"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    title: str = Field(nullable=False)
    description: Optional[str] = Field(default=None)
    due_date: Optional[date] = Field(default=None)
    priority: TaskPriority = Field(default="medium", sa_column=Column(String, nullable=False))
    status: TaskStatus = Field(default="todo", sa_column=Column(String, nullable=False))
    
    assigned_to: Optional[int] = Field(default=None, foreign_key="employees.id")
    assigned_by: Optional[int] = Field(default=None, foreign_key="users.id")
    
    estimated_hours: Optional[float] = Field(default=None)
    tags: list[str] = Field(
        sa_column=Column(ARRAY(String), nullable=False, default=[]),
    )
    
    is_recurring: bool = Field(default=False)
    recurrence_pattern: Optional[TaskRecurrencePattern] = Field(default=None, sa_column=Column(String, nullable=True))
    recurrence_interval_days: Optional[int] = Field(default=None)
    recurrence_day_of_week: Optional[int] = Field(default=None)
    recurrence_day_of_month: Optional[int] = Field(default=None)
    
    parent_task_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="tasks.id",
    )
    
    deleted_at: Optional[datetime] = Field(default=None)
    deleted_by: Optional[int] = Field(default=None, foreign_key="users.id")
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TaskSubtask(SQLModel, table=True):
    """Task subtask/checklist database model."""
    __tablename__ = "task_subtasks"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    task_id: uuid.UUID = Field(
        foreign_key="tasks.id",
        nullable=False,
    )
    title: str = Field(nullable=False)
    is_done: bool = Field(default=False)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TaskComment(SQLModel, table=True):
    """Task comment database model."""
    __tablename__ = "task_comments"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    task_id: uuid.UUID = Field(
        foreign_key="tasks.id",
        nullable=False,
    )
    author_id: int = Field(foreign_key="users.id", nullable=False)
    content: str = Field(nullable=False)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TaskTimeLog(SQLModel, table=True):
    """Task time log database model."""
    __tablename__ = "task_time_logs"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    task_id: uuid.UUID = Field(
        foreign_key="tasks.id",
        nullable=False,
    )
    employee_id: int = Field(foreign_key="employees.id", nullable=False)
    hours: float = Field(nullable=False)
    note: Optional[str] = Field(default=None)
    
    logged_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
