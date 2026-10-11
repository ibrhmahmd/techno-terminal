"""Competitions HTTP-layer service factories (ADR-0002: api/ → services/)."""

from fastapi import Depends

from app.api.dependencies import UoW
from app.modules.competitions import (
    CompetitionNotifier,
    CompetitionService,
    TeamPlacementService,
    TeamRegistrationService,
    TeamRosterService,
    TeamService,
)


def get_competition_service(uow: UoW) -> CompetitionService:
    return CompetitionService(uow)


def get_competition_notifier() -> CompetitionNotifier:
    """CompetitionNotifier provider — overridden in create_app() with the real adapter."""
    raise NotImplementedError("wired in create_app()")


def get_team_service(
    uow: UoW,
    notifier: CompetitionNotifier = Depends(get_competition_notifier),
) -> TeamService:
    """Returns a fresh TeamService instance with the notifier port."""
    return TeamService(uow, notifier=notifier)


def get_team_registration_service(
    uow: UoW,
    notifier: CompetitionNotifier = Depends(get_competition_notifier),
) -> TeamRegistrationService:
    return TeamRegistrationService(uow, notifier=notifier)


def get_team_roster_service(
    uow: UoW,
    notifier: CompetitionNotifier = Depends(get_competition_notifier),
) -> TeamRosterService:
    return TeamRosterService(uow, notifier=notifier)


def get_team_placement_service(
    uow: UoW,
    notifier: CompetitionNotifier = Depends(get_competition_notifier),
) -> TeamPlacementService:
    return TeamPlacementService(uow, notifier=notifier)
