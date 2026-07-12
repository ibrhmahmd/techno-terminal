"""Task API Router

Exposes CRUD endpoints for task tracking.
Mounted under /api/v1
"""
import uuid
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.api.schemas.common import ApiResponse
from app.modules.tasks import (
    TaskService,
    CreateTaskInput,
    UpdateTaskInput,
    TaskReadDTO,
    TaskDetailDTO,
    TaskStatus,
    TaskPriority,
    CreateTaskSubtaskInput,
    UpdateTaskSubtaskInput,
    TaskSubtaskReadDTO,
    CreateTaskCommentInput,
    TaskCommentReadDTO,
    CreateTaskTimeLogInput,
    TaskTimeLogReadDTO
)
from app.api.dependencies import require_admin, require_any, get_task_service
from app.modules.auth import User

router = APIRouter(tags=["Tasks"])


@router.post("/tasks", response_model=ApiResponse[TaskDetailDTO], summary="Create a new task")
def create_task(
    dto: CreateTaskInput,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    service: TaskService = Depends(get_task_service)
):
    """Creates a new task. Restricted to admins."""
    result = service.create_task(dto, current_user, background_tasks=background_tasks)
    return ApiResponse(data=result, message="Task created successfully")


@router.get("/tasks", response_model=ApiResponse[list[TaskReadDTO]], summary="List all tasks")
def list_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by task priority"),
    assigned_to: Optional[int] = Query(None, description="Filter by assignee employee ID"),
    is_recurring: Optional[bool] = Query(None, description="Filter by recurrence status"),
    current_user: User = Depends(require_any),
    service: TaskService = Depends(get_task_service)
):
    """Lists all tasks with optional filters. Accessible by any authenticated user."""
    result = service.list_tasks(
        current_user=current_user,
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        is_recurring=is_recurring
    )
    return ApiResponse(data=result, message=f"Fetched {len(result)} tasks")


@router.get("/tasks/{task_id}", response_model=ApiResponse[TaskDetailDTO], summary="Get task detail")
def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(require_any),
    service: TaskService = Depends(get_task_service)
):
    """Retrieves detailed information of a task including subtasks, comments, and time logs."""
    result = service.get_task(task_id, current_user)
    return ApiResponse(data=result)


@router.patch("/tasks/{task_id}", response_model=ApiResponse[TaskDetailDTO], summary="Update a task")
def update_task(
    task_id: uuid.UUID,
    dto: UpdateTaskInput,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_any),
    service: TaskService = Depends(get_task_service)
):
    """Updates a task. Admins have full access. Assigned employees can update status only."""
    result = service.update_task(task_id, dto, current_user, background_tasks=background_tasks)
    return ApiResponse(data=result, message="Task updated successfully")


@router.delete("/tasks/{task_id}", response_model=ApiResponse[bool], summary="Soft delete a task")
def delete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    service: TaskService = Depends(get_task_service)
):
    """Soft deletes a task. Restricted to admins."""
    service.soft_delete(task_id, current_user)
    return ApiResponse(data=True, message="Task deleted successfully")


@router.post("/tasks/{task_id}/subtasks", response_model=ApiResponse[TaskSubtaskReadDTO], summary="Create a new subtask")
def add_subtask(
    task_id: uuid.UUID,
    dto: CreateTaskSubtaskInput,
    current_user: User = Depends(require_admin),
    service: TaskService = Depends(get_task_service)
):
    """Adds a subtask to a task. Restricted to admins."""
    subtask = service.add_subtask(task_id, dto, current_user)
    return ApiResponse(data=TaskSubtaskReadDTO.model_validate(subtask), message="Subtask added successfully")


@router.patch("/tasks/subtasks/{subtask_id}", response_model=ApiResponse[TaskSubtaskReadDTO], summary="Update a subtask")
def update_subtask(
    subtask_id: uuid.UUID,
    dto: UpdateTaskSubtaskInput,
    current_user: User = Depends(require_any),
    service: TaskService = Depends(get_task_service)
):
    """Updates a subtask. Admins have full access. Assigned employees can update completion status only."""
    subtask = service.update_subtask(subtask_id, dto, current_user)
    return ApiResponse(data=TaskSubtaskReadDTO.model_validate(subtask), message="Subtask updated successfully")


@router.delete("/tasks/subtasks/{subtask_id}", response_model=ApiResponse[bool], summary="Delete a subtask")
def delete_subtask(
    subtask_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    service: TaskService = Depends(get_task_service)
):
    """Deletes a subtask. Restricted to admins."""
    service.delete_subtask(subtask_id, current_user)
    return ApiResponse(data=True, message="Subtask deleted successfully")


@router.post("/tasks/{task_id}/comments", response_model=ApiResponse[TaskCommentReadDTO], summary="Add a comment")
def add_comment(
    task_id: uuid.UUID,
    dto: CreateTaskCommentInput,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_any),
    service: TaskService = Depends(get_task_service)
):
    """Adds a comment to a task. Admin or assigned employee only."""
    comment = service.add_comment(task_id, dto, current_user, background_tasks=background_tasks)
    
    # Resolve author name
    author_name = current_user.username
    if current_user.employee_id:
        from app.modules.hr.models.employee_models import Employee
        emp = service._uow._session.get(Employee, current_user.employee_id)
        if emp:
            author_name = emp.full_name
            
    result = TaskCommentReadDTO(
        id=comment.id,
        task_id=comment.task_id,
        author_id=comment.author_id,
        author_name=author_name,
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at
    )
    return ApiResponse(data=result, message="Comment added successfully")


@router.delete("/tasks/comments/{comment_id}", response_model=ApiResponse[bool], summary="Delete a comment")
def delete_comment(
    comment_id: uuid.UUID,
    current_user: User = Depends(require_any),
    service: TaskService = Depends(get_task_service)
):
    """Deletes a comment. Author or admin only."""
    service.delete_comment(comment_id, current_user)
    return ApiResponse(data=True, message="Comment deleted successfully")


@router.post("/tasks/{task_id}/time-logs", response_model=ApiResponse[TaskTimeLogReadDTO], summary="Log time spent on task")
def add_time_log(
    task_id: uuid.UUID,
    dto: CreateTaskTimeLogInput,
    current_user: User = Depends(require_any),
    service: TaskService = Depends(get_task_service)
):
    """Logs hours spent on a task. Assigned employee only."""
    log = service.add_time_log(task_id, dto, current_user)
    
    # Resolve employee name
    employee_name = None
    if current_user.employee_id:
        from app.modules.hr.models.employee_models import Employee
        emp = service._uow._session.get(Employee, current_user.employee_id)
        if emp:
            employee_name = emp.full_name
            
    result = TaskTimeLogReadDTO(
        id=log.id,
        task_id=log.task_id,
        employee_id=log.employee_id,
        employee_name=employee_name or f"Employee #{log.employee_id}",
        hours=log.hours,
        note=log.note,
        logged_at=log.logged_at,
        created_at=log.created_at
    )
    return ApiResponse(data=result, message="Time logged successfully")
