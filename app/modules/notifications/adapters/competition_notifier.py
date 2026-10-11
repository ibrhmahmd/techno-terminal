"""Adapter implementing CompetitionNotifier using NotificationService (ADR-0007)."""

from typing import Optional

from fastapi import BackgroundTasks, Depends

from app.api.dependencies import get_notification_service
from app.modules.competitions import CompetitionNotifier
from app.modules.notifications.services.notification_service import NotificationService


class NotificationServiceCompetitionNotifier:
    """Adapts NotificationService to the CompetitionNotifier port."""

    def __init__(self, background_tasks: BackgroundTasks, notif_svc: NotificationService):
        self._background_tasks = background_tasks
        self._notif_svc = notif_svc

    def team_registration(
        self,
        *,
        student_id: int,
        team_id: int,
        team_name: str,
        competition_name: str,
        category: str,
        subcategory: Optional[str],
    ) -> None:
        self._notif_svc.competition.notify_team_registration(
            student_id=student_id,
            team_id=team_id,
            team_name=team_name,
            competition_name=competition_name,
            category=category,
            subcategory=subcategory,
            background_tasks=self._background_tasks,
        )

    def placement_announcement(
        self,
        *,
        student_id: int,
        team_id: int,
        team_name: str,
        competition_name: str,
        placement_rank: int,
        placement_label: Optional[str],
    ) -> None:
        self._notif_svc.competition.notify_placement_announcement(
            student_id=student_id,
            team_id=team_id,
            team_name=team_name,
            competition_name=competition_name,
            placement_rank=placement_rank,
            placement_label=placement_label,
            background_tasks=self._background_tasks,
        )


def get_competition_notifier(
    background_tasks: BackgroundTasks,
    notif_svc: NotificationService = Depends(get_notification_service),
) -> CompetitionNotifier:
    """FastAPI dependency factory for the CompetitionNotifier adapter."""
    return NotificationServiceCompetitionNotifier(
        background_tasks=background_tasks, notif_svc=notif_svc
    )
