"""Competitions HTTP-layer service factories (ADR-0002: api/ → services/)."""

from fastapi import Depends

from app.api.dependencies import get_notification_service
from app.modules.competitions import CompetitionService, TeamService


def get_competition_service() -> CompetitionService:
    """Returns a fresh CompetitionService instance per request."""
    return CompetitionService()


def get_team_service(
    notification_svc: "NotificationService" = Depends(get_notification_service),
) -> TeamService:
    """Returns a fresh TeamService instance with notification support."""
    return TeamService(notification_svc=notification_svc)
