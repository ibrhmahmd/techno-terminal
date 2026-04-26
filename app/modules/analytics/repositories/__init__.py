"""
app/modules/analytics/repositories/__init__.py
──────────────────────────────────────────────
Exports all Analytics data access components.
"""

from .financial_repository import (
    get_revenue_by_date,
    get_revenue_by_method,
    get_outstanding_by_group,
    get_top_debtors,
)
from .academic_repository import (
    get_active_enrollment_count,
    get_today_unpaid_attendees,
    get_attendance_heatmap,
)
from .competition_repository import (
    get_competition_fee_summary,
)
from .bi_repository import (
    get_new_enrollments_trend,
    get_retention_metrics,
    get_instructor_performance,
    get_level_retention_funnel,
    get_instructor_value_matrix,
    get_schedule_utilization,
    get_flight_risk_students,
)
