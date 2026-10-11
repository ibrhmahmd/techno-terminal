"""
app/modules/analytics/services/competition_service.py
─────────────────────────────────────────────────────
Domain service for competition analytics.
"""

from app.db.uow import UnitOfWork
from app.modules.analytics.repositories.competition_repository import CompetitionRepository
from app.modules.analytics.schemas import CompetitionFeeSummaryDTO


class CompetitionAnalyticsService:
    """Service handling competition participation and fee metrics."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._repo = CompetitionRepository(uow.session)

    def get_competition_fee_summary(self) -> list[CompetitionFeeSummaryDTO]:
        return self._repo.get_competition_fee_summary()
