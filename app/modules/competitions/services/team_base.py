"""Shared plumbing for the team services."""
import logging
from typing import Optional

from app.db.uow import UnitOfWork
from app.modules.competitions.ports import CompetitionNotifier
from app.modules.competitions.repositories.competition_repository import CompetitionRepository
from app.modules.competitions.repositories.team_repository import TeamRepository

logger = logging.getLogger(__name__)


class TeamServiceBase:
    """Holds the Unit of Work, repositories and the post-commit notifier call."""

    def __init__(self, uow: UnitOfWork, notifier: Optional[CompetitionNotifier] = None) -> None:
        self._uow = uow
        self._notifier = notifier
        self._teams = TeamRepository(uow.session)
        self._comps = CompetitionRepository(uow.session)

    def _notify(self, method: str, **kwargs) -> None:
        """Call the notifier after commit; failures are logged, never raised."""
        if self._notifier is None:
            return
        try:
            getattr(self._notifier, method)(**kwargs)
        except Exception:
            logger.exception("Competition notifier %s failed", method)
