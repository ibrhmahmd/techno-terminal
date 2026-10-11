"""Competitions module ports (ADR-0007)."""

from typing import Optional, Protocol


class CompetitionNotifier(Protocol):
    """Port for competition notifications, called after the use case commits.

    Implementations must not raise; the caller logs and swallows failures.
    """

    def team_registration(
        self,
        *,
        student_id: int,
        team_id: int,
        team_name: str,
        competition_name: str,
        category: str,
        subcategory: Optional[str],
    ) -> None: ...

    def placement_announcement(
        self,
        *,
        student_id: int,
        team_id: int,
        team_name: str,
        competition_name: str,
        placement_rank: int,
        placement_label: Optional[str],
    ) -> None: ...
