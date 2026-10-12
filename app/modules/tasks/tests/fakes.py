"""Test fake for the TaskNotifier port."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FakeTaskNotifier:
    """Records every call as (method_name, kwargs) for test assertions."""

    calls: list[tuple[str, dict]] = field(default_factory=list)
    should_raise: bool = False
    raise_exception: Optional[Exception] = None

    def _record(self, name: str, **kwargs) -> None:
        if self.should_raise:
            raise self.raise_exception or RuntimeError("Notifier failure")
        self.calls.append((name, kwargs))

    def task_assigned(self, **kwargs) -> None:
        self._record("task_assigned", **kwargs)

    def task_status_changed(self, **kwargs) -> None:
        self._record("task_status_changed", **kwargs)

    def task_comment_added(self, **kwargs) -> None:
        self._record("task_comment_added", **kwargs)

    def reset(self) -> None:
        self.calls.clear()
