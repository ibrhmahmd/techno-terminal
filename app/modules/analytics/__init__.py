"""
app/modules/analytics/__init__.py
──────────────────────────────────
Analytics Module Public API Facade.
Re-exports the 16 original metrics functions to maintain 100% backward
compatibility with UI downstream consumers (e.g. 9_Reports.py), but now
returns strongly-typed Pydantic DTOs instead of raw dictionaries.
"""

from .services.financial_service import FinancialAnalyticsService
from .services.academic_service import AcademicAnalyticsService
from .services.competition_service import CompetitionAnalyticsService
from .services.bi_service import BIAnalyticsService

_fin_svc = FinancialAnalyticsService()
_acad_svc = AcademicAnalyticsService()
_comp_svc = CompetitionAnalyticsService()
_bi_svc = BIAnalyticsService()

# ── Financial ─────────────────────────────────────────────────────────────────
get_revenue_by_date = _fin_svc.get_revenue_by_date
get_revenue_by_method = _fin_svc.get_revenue_by_method
get_outstanding_by_group = _fin_svc.get_outstanding_by_group
get_top_debtors = _fin_svc.get_top_debtors

# ── Academic ──────────────────────────────────────────────────────────────────
get_active_enrollment_count = _acad_svc.get_active_enrollment_count
get_today_sessions = _acad_svc.get_today_sessions
get_today_unpaid_attendees = _acad_svc.get_today_unpaid_attendees
get_group_roster = _acad_svc.get_group_roster
get_attendance_heatmap = _acad_svc.get_attendance_heatmap

# ── Competition ───────────────────────────────────────────────────────────────
get_competition_fee_summary = _comp_svc.get_competition_fee_summary

# ── Business Intelligence (BI) ────────────────────────────────────────────────
get_new_enrollments_trend = _bi_svc.get_new_enrollments_trend
get_retention_metrics = _bi_svc.get_retention_metrics
get_instructor_performance = _bi_svc.get_instructor_performance
get_level_retention_funnel = _bi_svc.get_level_retention_funnel
get_instructor_value_matrix = _bi_svc.get_instructor_value_matrix
get_schedule_utilization = _bi_svc.get_schedule_utilization
get_flight_risk_students = _bi_svc.get_flight_risk_students

__all__ = [
    "get_revenue_by_date",
    "get_revenue_by_method",
    "get_outstanding_by_group",
    "get_top_debtors",
    "get_active_enrollment_count",
    "get_today_sessions",
    "get_today_unpaid_attendees",
    "get_group_roster",
    "get_attendance_heatmap",
    "get_competition_fee_summary",
    "get_new_enrollments_trend",
    "get_retention_metrics",
    "get_instructor_performance",
    "get_level_retention_funnel",
    "get_instructor_value_matrix",
    "get_schedule_utilization",
    "get_flight_risk_students",
]
