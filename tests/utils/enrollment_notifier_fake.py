"""Test fake for the EnrollmentNotifier port."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FakeEnrollmentNotifier:
    """Records every call as (method_name, kwargs) for test assertions."""

    calls: list[tuple[str, dict]] = field(default_factory=list)
    should_raise: bool = False
    raise_exception: Optional[Exception] = None

    def _record(self, name: str, **kwargs) -> None:
        if self.should_raise:
            raise self.raise_exception or RuntimeError("Notifier failure")
        self.calls.append((name, kwargs))

    def enrollment_created(self, **kwargs) -> None:
        self._record("enrollment_created", **kwargs)

    def enrollment_updated(self, **kwargs) -> None:
        self._record("enrollment_updated", **kwargs)

    def enrollment_transferred(self, **kwargs) -> None:
        self._record("enrollment_transferred", **kwargs)

    def enrollment_dropped(self, **kwargs) -> None:
        self._record("enrollment_dropped", **kwargs)

    def reset(self) -> None:
        self.calls.clear()
