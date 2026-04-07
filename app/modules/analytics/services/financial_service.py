"""
app/modules/analytics/services/financial_service.py
───────────────────────────────────────────────────
Domain service for financial analytics.
"""

from datetime import date
from app.db.connection import get_session
import app.modules.analytics.repositories.financial_repository as repo
from app.modules.analytics.schemas import (
    RevenueByDateDTO,
    RevenueByMethodDTO,
    OutstandingByGroupDTO,
    TopDebtorDTO,
    RevenueMetricsDTO,
    RevenueForecastDTO,
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

    def get_revenue_metrics(self, months: int = 6) -> RevenueMetricsDTO:
        """Get extended revenue metrics with trend analysis."""
        with get_session() as db:
            return repo.get_revenue_metrics(db, months)

    def get_revenue_forecast(self, months_ahead: int = 3) -> list[RevenueForecastDTO]:
        """Get revenue forecast for future months."""
        with get_session() as db:
            return repo.get_revenue_forecast(db, months_ahead)
