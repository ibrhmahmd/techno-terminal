"""Tasks module ports (ADR-0007)."""

import uuid
from typing import Optional, Protocol


class TaskNotifier(Protocol):
    """Port for task notifications, called after the use case commits.

    Implementations must not raise; the caller logs and swallows failures.
    """

    def task_assigned(
        self, *, task_id: uuid.UUID, employee_id: int, assigned_by_user_id: Optional[int]
    ) -> None: ...

    def task_status_changed(
        self,
        *,
        task_id: uuid.UUID,
        employee_id: Optional[int],
        old_status: str,
        new_status: str,
        changed_by_user_id: Optional[int],
    ) -> None: ...

    def task_comment_added(
        self, *, task_id: uuid.UUID, comment_id: uuid.UUID, author_user_id: int
    ) -> None: ...
