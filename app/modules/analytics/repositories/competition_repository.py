"""
app/modules/analytics/repositories/competition_repository.py
────────────────────────────────────────────────────────────
Data access layer for competition analytics.
"""

from sqlmodel import Session
from sqlalchemy import text
from app.modules.analytics.schemas import CompetitionFeeSummaryDTO


def get_competition_fee_summary(db: Session) -> list[CompetitionFeeSummaryDTO]:
    """Per-competition: teams, members, fees collected vs owed."""
    stmt = text("""
        SELECT
            cp.id AS competition_id,
            cp.name AS competition_name,
            cp.competition_date,
            COUNT(DISTINCT t.id) AS team_count,
            COUNT(DISTINCT tm.id) AS member_count,
            COALESCE(SUM(t.enrollment_fee_per_student) FILTER (WHERE tm.fee_paid = TRUE), 0) AS fees_collected,
            COALESCE(SUM(t.enrollment_fee_per_student) FILTER (WHERE tm.fee_paid = FALSE
                AND t.enrollment_fee_per_student IS NOT NULL), 0) AS fees_outstanding
        FROM competitions cp
        LEFT JOIN competition_categories cc ON cc.competition_id = cp.id
        LEFT JOIN teams t ON t.category_id = cc.id
        LEFT JOIN team_members tm ON tm.team_id = t.id
        GROUP BY cp.id, cp.name, cp.competition_date
        ORDER BY cp.competition_date DESC NULLS LAST, cp.id DESC
    """)
    rows = db.execute(stmt).all()
    return [CompetitionFeeSummaryDTO(**r._mapping) for r in rows]
