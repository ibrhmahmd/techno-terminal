"""Test fake for the CompetitionNotifier port."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FakeCompetitionNotifier:
    """Records every call as (method_name, kwargs) for test assertions."""

    calls: list[tuple[str, dict]] = field(default_factory=list)
    should_raise: bool = False
    raise_exception: Optional[Exception] = None

    def _record(self, name: str, **kwargs) -> None:
        if self.should_raise:
            raise self.raise_exception or RuntimeError("Notifier failure")
        self.calls.append((name, kwargs))

    def team_registration(self, **kwargs) -> None:
        self._record("team_registration", **kwargs)

    def placement_announcement(self, **kwargs) -> None:
        self._record("placement_announcement", **kwargs)

    def reset(self) -> None:
        self.calls.clear()
