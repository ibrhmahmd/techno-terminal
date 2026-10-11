"""Competitions HTTP-layer service factories (ADR-0002: api/ → services/)."""

from fastapi import Depends

from app.modules.competitions import CompetitionNotifier, CompetitionService, TeamService


def get_competition_service() -> CompetitionService:
    """Returns a fresh CompetitionService instance per request."""
    return CompetitionService()


def get_competition_notifier() -> CompetitionNotifier:
    """CompetitionNotifier provider — overridden in create_app() with the real adapter."""
    raise NotImplementedError("wired in create_app()")


def get_team_service(
    notifier: CompetitionNotifier = Depends(get_competition_notifier),
) -> TeamService:
    """Returns a fresh TeamService instance with the notifier port."""
    return TeamService(notifier=notifier)
