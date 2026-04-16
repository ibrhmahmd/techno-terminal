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


# ── Financial ─────────────────────────────────────────────────────────────────
def get_revenue_by_date(*args, **kwargs):
    return FinancialAnalyticsService().get_revenue_by_date(*args, **kwargs)

def get_revenue_by_method(*args, **kwargs):
    return FinancialAnalyticsService().get_revenue_by_method(*args, **kwargs)

def get_outstanding_by_group(*args, **kwargs):
    return FinancialAnalyticsService().get_outstanding_by_group(*args, **kwargs)

def get_top_debtors(*args, **kwargs):
    return FinancialAnalyticsService().get_top_debtors(*args, **kwargs)


# ── Academic ──────────────────────────────────────────────────────────────────
def get_active_enrollment_count(*args, **kwargs):
    return AcademicAnalyticsService().get_active_enrollment_count(*args, **kwargs)

def get_today_sessions(*args, **kwargs):
    return AcademicAnalyticsService().get_today_sessions(*args, **kwargs)

def get_today_unpaid_attendees(*args, **kwargs):
    return AcademicAnalyticsService().get_today_unpaid_attendees(*args, **kwargs)

def get_group_roster(*args, **kwargs):
    return AcademicAnalyticsService().get_group_roster(*args, **kwargs)

def get_attendance_heatmap(*args, **kwargs):
    return AcademicAnalyticsService().get_attendance_heatmap(*args, **kwargs)


# ── Competition ───────────────────────────────────────────────────────────────
def get_competition_fee_summary(*args, **kwargs):
    return CompetitionAnalyticsService().get_competition_fee_summary(*args, **kwargs)


# ── Business Intelligence (BI) ────────────────────────────────────────────────
def get_new_enrollments_trend(*args, **kwargs):
    return BIAnalyticsService().get_new_enrollments_trend(*args, **kwargs)

def get_retention_metrics(*args, **kwargs):
    return BIAnalyticsService().get_retention_metrics(*args, **kwargs)

def get_instructor_performance(*args, **kwargs):
    return BIAnalyticsService().get_instructor_performance(*args, **kwargs)

def get_level_retention_funnel(*args, **kwargs):
    return BIAnalyticsService().get_level_retention_funnel(*args, **kwargs)

def get_instructor_value_matrix(*args, **kwargs):
    return BIAnalyticsService().get_instructor_value_matrix(*args, **kwargs)

def get_schedule_utilization(*args, **kwargs):
    return BIAnalyticsService().get_schedule_utilization(*args, **kwargs)

def get_flight_risk_students(*args, **kwargs):
    return BIAnalyticsService().get_flight_risk_students(*args, **kwargs)


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
