"""
app/modules/analytics/services/financial_service.py
───────────────────────────────────────────────────
Domain service for financial analytics.
"""

from datetime import date
from app.db.connection import get_session
from app.modules.analytics.repositories import financial_repository as repo
from app.modules.analytics.schemas import (
    RevenueByDateDTO,
    RevenueByMethodDTO,
    OutstandingByGroupDTO,
    TopDebtorDTO,
)


class FinancialAnalyticsService:
    """Service handling financial metrics and revenue reporting."""

    def get_revenue_by_date(self, start: date, end: date) -> list[RevenueByDateDTO]:
        with get_session() as db:
            return repo.get_revenue_by_date(db, start, end)

    def get_revenue_by_method(self, start: date, end: date) -> list[RevenueByMethodDTO]:
        with get_session() as db:
            return repo.get_revenue_by_method(db, start, end)

    def get_outstanding_by_group(self) -> list[OutstandingByGroupDTO]:
        with get_session() as db:
            return repo.get_outstanding_by_group(db)

    def get_top_debtors(self, limit: int = 15) -> list[TopDebtorDTO]:
        with get_session() as db:
            return repo.get_top_debtors(db, limit)
