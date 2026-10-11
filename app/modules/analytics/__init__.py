"""
app/modules/analytics/__init__.py
─────────────────────────────────
Analytics Module Facade (ADR-0003). Analytics sits at the top of the module order and is
read-only: its use cases never commit and it owns no tables.

Exports the five service classes; nothing else in the module is meant to be imported
from outside.
"""

from app.modules.analytics.services.academic_service import AcademicAnalyticsService
from app.modules.analytics.services.bi_service import BIAnalyticsService
from app.modules.analytics.services.competition_service import CompetitionAnalyticsService
from app.modules.analytics.services.dashboard_service import DashboardService
from app.modules.analytics.services.financial_service import FinancialAnalyticsService

__all__ = [
    "AcademicAnalyticsService",
    "BIAnalyticsService",
    "CompetitionAnalyticsService",
    "DashboardService",
    "FinancialAnalyticsService",
]
