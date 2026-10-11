"""
app/modules/analytics/repositories/competition_repository.py
────────────────────────────────────────────────────────────
Data access layer for competition analytics.
"""

from sqlmodel import Session
from sqlalchemy import text
from app.modules.analytics.schemas import CompetitionFeeSummaryDTO


class CompetitionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_competition_fee_summary(self) -> list[CompetitionFeeSummaryDTO]:
        """Per-competition: teams, members, fees collected vs owed."""
        stmt = text("""
            SELECT
                cp.id AS competition_id,
                cp.name AS competition_name,
                cp.competition_date,
                COUNT(DISTINCT t.id) AS team_count,
                COUNT(DISTINCT tm.id) AS member_count,
                COALESCE(SUM(tm.amount_paid) FILTER (WHERE tm.amount_paid > 0), 0) AS fees_collected,
                COALESCE(SUM(tm.amount_due - tm.amount_paid) FILTER (WHERE tm.amount_due > tm.amount_paid), 0) AS fees_outstanding
            FROM competitions cp
            LEFT JOIN teams t ON t.competition_id = cp.id
            LEFT JOIN team_members tm ON tm.team_id = t.id
            GROUP BY cp.id, cp.name, cp.competition_date
            ORDER BY cp.competition_date DESC NULLS LAST, cp.id DESC
        """)
        rows = self._session.execute(stmt).all()
        return [CompetitionFeeSummaryDTO(**r._mapping) for r in rows]
