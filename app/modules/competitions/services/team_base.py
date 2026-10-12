"""Shared plumbing for the team services."""
import logging
from typing import Optional

from app.db.uow import UnitOfWork
from app.modules.crm import LogCompetitionRegistrationDTO, StudentActivityService
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

    def _log_team_registration_activity(
        self,
        team,
        student_ids: list[int],
        competition_name: str,
        current_user_id: Optional[int],
    ) -> None:
        """Log a competition-registration activity per student in the shared unit of work
        (ADR-0009); the calling use case commits. Failures are logged, never raised."""
        try:
            activity_svc = StudentActivityService(self._uow)
            for sid in student_ids:
                activity_svc.log_competition_registration(
                    LogCompetitionRegistrationDTO(
                        student_id=sid,
                        competition_id=team.competition_id,
                        competition_name=competition_name,
                        performed_by=current_user_id,
                    )
                )
        except Exception:
            logger.exception("Failed to log competition registration activity for team %s", team.id)
