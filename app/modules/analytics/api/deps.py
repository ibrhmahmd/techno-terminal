"""Analytics HTTP-layer service factories (ADR-0002: api/ → services/).

Analytics is read-only: its use cases never commit.
"""

from app.api.dependencies import UoW
from app.modules.analytics.services.academic_service import AcademicAnalyticsService
from app.modules.analytics.services.bi_service import BIAnalyticsService
from app.modules.analytics.services.competition_service import CompetitionAnalyticsService
from app.modules.analytics.services.dashboard_service import DashboardService
from app.modules.analytics.services.financial_service import FinancialAnalyticsService


def get_academic_analytics_service(uow: UoW) -> AcademicAnalyticsService:
    return AcademicAnalyticsService(uow)


def get_dashboard_service(uow: UoW) -> DashboardService:
    return DashboardService(uow)


def get_financial_analytics_service(uow: UoW) -> FinancialAnalyticsService:
    return FinancialAnalyticsService(uow)


def get_bi_analytics_service(uow: UoW) -> BIAnalyticsService:
    return BIAnalyticsService(uow)


def get_competition_analytics_service(uow: UoW) -> CompetitionAnalyticsService:
    return CompetitionAnalyticsService(uow)
