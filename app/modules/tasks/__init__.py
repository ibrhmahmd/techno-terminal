"""
app/modules/tasks/__init__.py
─────────────────────────────
Tasks Module Facade (ADR-0003)

Other modules must import Tasks ONLY via this facade, except
app.modules.tasks.models which anyone may import (ADR-0004).
"""
from app.modules.tasks.models import (
    Task,
    TaskSubtask,
    TaskComment,
    TaskTimeLog,
    TaskStatus,
    TaskPriority,
    TaskRecurrencePattern,
)
from app.modules.tasks.ports import TaskNotifier
from app.modules.tasks.schemas.task_schemas import (
    CreateTaskInput,
    UpdateTaskInput,
    TaskReadDTO,
    TaskDetailDTO,
    CreateTaskSubtaskInput,
    UpdateTaskSubtaskInput,
    TaskSubtaskReadDTO,
    CreateTaskCommentInput,
    TaskCommentReadDTO,
    CreateTaskTimeLogInput,
    TaskTimeLogReadDTO,
)
from app.modules.tasks.scheduler import start_task_scheduler
from app.modules.tasks.services.task_service import TaskService

__all__ = [
    "Task",
    "TaskSubtask",
    "TaskComment",
    "TaskTimeLog",
    "TaskStatus",
    "TaskPriority",
    "TaskRecurrencePattern",
    "TaskNotifier",
    "TaskService",
    "start_task_scheduler",
    "CreateTaskInput",
    "UpdateTaskInput",
    "TaskReadDTO",
    "TaskDetailDTO",
    "CreateTaskSubtaskInput",
    "UpdateTaskSubtaskInput",
    "TaskSubtaskReadDTO",
    "CreateTaskCommentInput",
    "TaskCommentReadDTO",
    "CreateTaskTimeLogInput",
    "TaskTimeLogReadDTO",
]
