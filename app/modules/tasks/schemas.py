"""Task Schemas

Pydantic DTOs for Task module operations.
Following the contract:
- Input DTO naming: {Operation}{Entity}Input (e.g. CreateTaskInput, UpdateTaskInput)
- Read DTO naming: {Entity}{Qualifier}DTO (e.g. TaskReadDTO, TaskDetailDTO)
"""
import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.modules.tasks.models import TaskStatus, TaskPriority, TaskRecurrencePattern, TASK_STATUSES, TASK_PRIORITIES, TASK_RECURRENCE_PATTERNS


class CreateTaskInput(BaseModel):
    """Input DTO for creating a task."""
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    due_date: Optional[date] = None
    priority: TaskPriority = "medium"
    status: TaskStatus = "todo"
    assigned_to: Optional[int] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    tags: list[str] = Field(default_factory=list)
    
    # Recurrence fields
    is_recurring: bool = False
    recurrence_pattern: Optional[TaskRecurrencePattern] = None
    recurrence_interval_days: Optional[int] = Field(None, ge=1)
    recurrence_day_of_week: Optional[int] = Field(None, ge=0, le=6)
    recurrence_day_of_month: Optional[int] = Field(None, ge=1, le=31)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: TaskPriority) -> TaskPriority:
        if v not in TASK_PRIORITIES:
            raise ValueError(f"Priority must be one of {TASK_PRIORITIES}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: TaskStatus) -> TaskStatus:
        if v not in TASK_STATUSES:
            raise ValueError(f"Status must be one of {TASK_STATUSES}")
        return v

    @field_validator("recurrence_pattern")
    @classmethod
    def validate_pattern(cls, v: Optional[TaskRecurrencePattern]) -> Optional[TaskRecurrencePattern]:
        if v is not None and v not in TASK_RECURRENCE_PATTERNS:
            raise ValueError(f"Recurrence pattern must be one of {TASK_RECURRENCE_PATTERNS}")
        return v


class UpdateTaskInput(BaseModel):
    """Input DTO for updating a task."""
    model_config = ConfigDict(str_strip_whitespace=True)

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    due_date: Optional[date] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    assigned_to: Optional[int] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    tags: Optional[list[str]] = None
    
    # Recurrence fields
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[TaskRecurrencePattern] = None
    recurrence_interval_days: Optional[int] = Field(None, ge=1)
    recurrence_day_of_week: Optional[int] = Field(None, ge=0, le=6)
    recurrence_day_of_month: Optional[int] = Field(None, ge=1, le=31)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[TaskPriority]) -> Optional[TaskPriority]:
        if v is not None and v not in TASK_PRIORITIES:
            raise ValueError(f"Priority must be one of {TASK_PRIORITIES}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[TaskStatus]) -> Optional[TaskStatus]:
        if v is not None and v not in TASK_STATUSES:
            raise ValueError(f"Status must be one of {TASK_STATUSES}")
        return v


class TaskSubtaskReadDTO(BaseModel):
    """Read DTO for a task subtask."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    title: str
    is_done: bool
    created_at: datetime
    updated_at: datetime


class CreateTaskSubtaskInput(BaseModel):
    """Input DTO for creating a task subtask."""
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(..., min_length=1, max_length=255)


class UpdateTaskSubtaskInput(BaseModel):
    """Input DTO for updating a task subtask."""
    model_config = ConfigDict(str_strip_whitespace=True)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    is_done: Optional[bool] = None


class TaskCommentReadDTO(BaseModel):
    """Read DTO for a task comment."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    author_id: int
    author_name: Optional[str] = None
    content: str
    created_at: datetime
    updated_at: datetime


class CreateTaskCommentInput(BaseModel):
    """Input DTO for creating a task comment."""
    model_config = ConfigDict(str_strip_whitespace=True)
    content: str = Field(..., min_length=1, max_length=5000)


class TaskTimeLogReadDTO(BaseModel):
    """Read DTO for a task time log."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    employee_id: int
    employee_name: Optional[str] = None
    hours: float
    note: Optional[str] = None
    logged_at: datetime
    created_at: datetime


class CreateTaskTimeLogInput(BaseModel):
    """Input DTO for creating a task time log."""
    model_config = ConfigDict(str_strip_whitespace=True)
    hours: float = Field(..., gt=0)
    note: Optional[str] = Field(None, max_length=1000)


class TaskReadDTO(BaseModel):
    """Read DTO for a task (list view)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: TaskPriority
    status: TaskStatus
    assigned_to: Optional[int] = None
    assigned_to_name: Optional[str] = None
    assigned_by: Optional[int] = None
    assigned_by_name: Optional[str] = None
    estimated_hours: Optional[float] = None
    tags: list[str] = Field(default_factory=list)
    is_recurring: bool
    recurrence_pattern: Optional[TaskRecurrencePattern] = None
    parent_task_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class TaskDetailDTO(TaskReadDTO):
    """Read DTO for a task with nested details."""
    subtasks: list[TaskSubtaskReadDTO] = Field(default_factory=list)
    comments: list[TaskCommentReadDTO] = Field(default_factory=list)
    time_logs: list[TaskTimeLogReadDTO] = Field(default_factory=list)
