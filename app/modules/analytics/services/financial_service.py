"""
app/modules/analytics/services/financial_service.py
───────────────────────────────────────────────────
Domain service for financial analytics.
"""

from datetime import date
from app.db.uow import UnitOfWork
from app.modules.analytics.repositories.financial_repository import FinancialRepository
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

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._repo = FinancialRepository(uow.session)

    def get_revenue_by_date(self, start: date, end: date) -> list[RevenueByDateDTO]:
        return self._repo.get_revenue_by_date(start, end)

    def get_revenue_by_method(self, start: date, end: date) -> list[RevenueByMethodDTO]:
        return self._repo.get_revenue_by_method(start, end)

    def get_outstanding_by_group(self) -> list[OutstandingByGroupDTO]:
        return self._repo.get_outstanding_by_group()

    def get_top_debtors(self, limit: int = 15) -> list[TopDebtorDTO]:
        return self._repo.get_top_debtors(limit)

    def get_revenue_metrics(self, months: int = 6) -> RevenueMetricsDTO:
        """Get extended revenue metrics with trend analysis."""
        return self._repo.get_revenue_metrics(months)

    def get_revenue_forecast(self, months_ahead: int = 3) -> list[RevenueForecastDTO]:
        """Get revenue forecast for future months."""
        return self._repo.get_revenue_forecast(months_ahead)
