"""Audit module catalogue: the integrity scenarios and the dashboard views.

Pure data, read by the services (view allow-list) and by the Streamlit demo UI.
"""

SEVERITY_PRIORITY = {"ERROR": 0, "WARNING": 1, "INFO": 2}

# Audit scenarios definitions
SCENARIOS = [
    {
        "code": "A",
        "severity": "INFO",
        "label": "Zero-Charge Active Enrollments",
        "view": "v_audit_zero_charge_enrollments",
        "description": "Active enrollments where amount_due is NULL or 0 — possible free ride or data omission.",
        "tip": "Filter by date to exclude June 2026 bulk-import: WHERE enrolled_at >= '2026-07-01'",
    },
    {
        "code": "B",
        "severity": "WARNING",
        "label": "Overpaid Enrollments (Credit Balances)",
        "view": "v_audit_overpaid_enrollments",
        "description": "Net payments exceed net_due — possible duplicate payment or unrecorded refund.",
        "tip": "Check overpaid_by column — this is the exact EGP owed back.",
    },
    {
        "code": "C",
        "severity": "WARNING",
        "label": "Orphaned Payments (No Enrollment Link)",
        "view": "v_audit_orphaned_payments",
        "description": "course_level payments with no enrollment_id — money collected but unattributable.",
        "tip": "Check receipt_number to find the original transaction in Supabase.",
    },
    {
        "code": "D",
        "severity": "ERROR",
        "label": "Duplicate Active Enrollments",
        "view": "v_audit_duplicate_enrollments",
        "description": "Same student has >1 active enrollment in the same group — potential double charge.",
        "tip": "Check enrollment_ids to identify which record to deactivate.",
    },
    {
        "code": "E",
        "severity": "INFO",
        "label": "Active Enrollments on Dead Groups",
        "view": "v_audit_dead_group_enrollments",
        "description": "Enrollment is active but parent group is inactive, completed, or archived.",
        "tip": "Usually cleanup lag — verify if the student should be transferred or completed.",
    },
    {
        "code": "F",
        "severity": "WARNING",
        "label": "Dropped/Transferred with Unrefunded Balance",
        "view": "v_audit_unrefunded_exits",
        "description": "Student was dropped or transferred but never received a refund.",
        "tip": "Check net_collected — this is the exact EGP owed back to the student.",
    },
    {
        "code": "G",
        "severity": "INFO",
        "label": "Level Mismatch (No group_levels Row)",
        "view": "v_audit_level_mismatch",
        "description": "Enrollment references a (group, level) that has no group_levels row — breaks Round Cost report.",
        "tip": "Run Report 4 after fixing to confirm attribution restores correctly.",
    },
    {
        "code": "H",
        "severity": "ERROR",
        "label": "Active Payments for Soft-Deleted Students",
        "view": "v_audit_ghost_payments",
        "description": "Non-deleted payments for soft-deleted students — ghost money distorting revenue.",
        "tip": "These payments should be soft-deleted together with the student record.",
    },
    {
        "code": "I",
        "severity": "WARNING",
        "label": "Full or Over-Discounts (≥ 100%)",
        "view": "v_audit_overdiscounted_enrollments",
        "description": "discount_applied >= amount_due — effective free enrollment, likely a data error.",
        "tip": "Review notes column — if it's a scholarship, document it and exclude from future alerts.",
    },
]

# Finance views definitions
FINANCE_VIEWS = [
    {
        "key": "outstanding",
        "label": "💳 Outstanding Balances (AR)",
        "view": "v_finance_outstanding_balances",
        "description": "Every active enrollment where the student still owes money. Sort by balance_owed for collections priority.",
        "category": "Revenue & Collection",
        "tip": "This is your Accounts Receivable register — the underpaid mirror of Audit Scenario B.",
    },
    {
        "key": "monthly_revenue",
        "label": "📈 Monthly Revenue",
        "view": "v_finance_monthly_revenue",
        "description": "Revenue trend over time: gross collected, refunded, and net per month.",
        "category": "Revenue & Collection",
    },
    {
        "key": "by_course",
        "label": "📚 Revenue by Course",
        "view": "v_finance_revenue_by_course",
        "description": "Which courses earn the most? Billed, discounts, collected, outstanding, and collection rate %.",
        "category": "Revenue & Collection",
    },
    {
        "key": "collection_rate",
        "label": "📉 Collection Rate by Group",
        "view": "v_finance_collection_rate_by_group",
        "description": "Which groups have poor payment follow-through? Sort ascending for worst performers.",
        "category": "Revenue & Collection",
        "tip": "Groups below 80% collection rate should trigger a payment follow-up call.",
    },
    {
        "key": "payment_methods",
        "label": "💰 Payment Methods",
        "view": "v_finance_payment_method_breakdown",
        "description": "Cash vs card vs bank transfer distribution by month.",
        "category": "Revenue & Collection",
    },
    {
        "key": "contract_costs",
        "label": "👷 Contract Instructor Costs",
        "view": "v_finance_contract_instructor_costs",
        "description": "Payroll per round for contract instructors. instructor_cost = revenue × contract_percentage.",
        "category": "Payroll & Cost",
        "tip": "This is Report 4 (Round Cost) formalized as a permanent view.",
    },
    {
        "key": "parttime_alloc",
        "label": "🗓️ Part-Time Allocation",
        "view": "v_finance_part_time_group_allocation",
        "description": "Which groups each part-time instructor teaches — foundation for salary allocation.",
        "category": "Payroll & Cost",
    },
    {
        "key": "payroll_vs_revenue",
        "label": "📊 Payroll vs Revenue",
        "view": "v_finance_total_payroll_vs_revenue",
        "description": "Monthly estimated profit = revenue − contract costs − fixed staff salaries.",
        "category": "Payroll & Cost",
        "tip": "estimated_profit is a floor — excludes operational costs beyond payroll.",
    },
    {
        "key": "discounts",
        "label": "🏷️ Discount Impact",
        "view": "v_finance_discount_impact",
        "description": "Revenue leakage from discounts, grouped by month and course.",
        "category": "Discounts & Risk",
    },
    {
        "key": "high_risk",
        "label": "⚠️ High-Risk Balances (AR Aging)",
        "view": "v_finance_high_risk_balances",
        "description": "Active enrollments with unpaid balance AND enrolled > 30 days. Bucketed by 30-60, 60-90, 90+ days.",
        "category": "Discounts & Risk",
        "tip": "Students in the 60-90 and 90+ buckets need immediate outreach.",
    },
    {
        "key": "group_summary",
        "label": "🏫 Group Revenue Summary",
        "view": "v_finance_group_revenue_summary",
        "description": "Per-group P&L: total enrollments, billed, discounts, collected, and outstanding.",
        "category": "Group Health",
    },
    {
        "key": "waiting_potential",
        "label": "⏳ Waiting List Potential",
        "view": "v_finance_waiting_list_revenue_potential",
        "description": "Revenue forecast if all waiting students convert, estimated from active enrollment fees.",
        "category": "Group Health",
    },
]

FINANCE_CATEGORIES = ["Revenue & Collection", "Payroll & Cost", "Discounts & Risk", "Group Health"]

# Date column each audit view can be filtered on ("since" filter); None = no date filter.
AUDIT_DATE_COLUMNS = {
    "v_audit_zero_charge_enrollments": "enrolled_at",
    "v_audit_overpaid_enrollments": None,
    "v_audit_orphaned_payments": "paid_at",
    "v_audit_duplicate_enrollments": "first_enrolled",
    "v_audit_dead_group_enrollments": "enrolled_at",
    "v_audit_unrefunded_exits": None,
    "v_audit_level_mismatch": "enrolled_at",
    "v_audit_ghost_payments": "paid_at",
    "v_audit_overdiscounted_enrollments": "enrolled_at",
}

BI_VIEWS = [
    "v_bi_attendance_rate",
    "v_bi_avg_revenue_per_student",
    "v_bi_billed_vs_collected",
    "v_bi_contract_instructor_cost",
    "v_bi_contract_instructors_idle",
    "v_bi_course_performance",
    "v_bi_current_wait_duration",
    "v_bi_demographics_completeness",
    "v_bi_enrollment_status",
    "v_bi_founding_cohort_status",
    "v_bi_gender_age_breakdown",
    "v_bi_groups_over_capacity",
    "v_bi_headcount_by_type",
    "v_bi_instructor_load",
    "v_bi_kpi_header",
    "v_bi_monthly_revenue",
    "v_bi_new_students_monthly",
    "v_bi_payment_completeness",
    "v_bi_payment_method_mix",
    "v_bi_waiting_conversion_stats",
    "v_bi_waiting_list_by_month",
    "v_bi_waiting_list_summary",
    "v_bi_weekly_schedule",
]

# Every view the module may read. View and column names are interpolated into SQL,
# so only names on this list (and plain identifiers) are accepted.
ALLOWED_VIEWS = frozenset(
    ["v_audit_summary", "v_finance_summary"]
    + [s["view"] for s in SCENARIOS]
    + [f["view"] for f in FINANCE_VIEWS]
    + BI_VIEWS
)
