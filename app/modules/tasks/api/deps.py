"""Tasks HTTP-layer service factories (ADR-0002: api/ → services/)."""

from fastapi import Depends

from app.api.dependencies import UoW
from app.modules.tasks import TaskNotifier, TaskService


def get_task_notifier() -> TaskNotifier:
    """TaskNotifier provider — overridden in create_app() with the real adapter."""
    raise NotImplementedError("wired in create_app()")


def get_task_service(
    uow: UoW,
    notifier: TaskNotifier = Depends(get_task_notifier),
) -> TaskService:
    return TaskService(uow, notifier=notifier)
