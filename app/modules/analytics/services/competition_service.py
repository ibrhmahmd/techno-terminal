"""
app/modules/analytics/services/competition_service.py
─────────────────────────────────────────────────────
Domain service for competition analytics.
"""

from app.db.connection import get_session
from app.modules.analytics.repositories import competition_repository as repo
from app.modules.analytics.schemas import CompetitionFeeSummaryDTO


class CompetitionAnalyticsService:
    """Service handling competition participation and fee metrics."""

    def get_competition_fee_summary(self) -> list[CompetitionFeeSummaryDTO]:
        with get_session() as db:
            return repo.get_competition_fee_summary(db)
