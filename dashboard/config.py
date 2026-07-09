import os
import streamlit as st
import psycopg2
import psycopg2.extras
import pandas as pd
from datetime import date
from dotenv import load_dotenv

# Load env variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Severity definitions
SEVERITY_COLOR = {
    "ERROR":   "#FF4B4B",
    "WARNING": "#FFA500",
    "INFO":    "#4B9EFF",
}

SEVERITY_ICON = {
    "ERROR":   "🔴",
    "WARNING": "🟡",
    "INFO":    "🔵",
}

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
FINANCE_CATEGORY_ICONS = {
    "Revenue & Collection": "💰",
    "Payroll & Cost": "👷",
    "Discounts & Risk": "⚠️",
    "Group Health": "🏫",
}

# Database functions
@st.cache_resource
def get_connection():
    return psycopg2.connect(DATABASE_URL)

def query(sql: str, params=None) -> pd.DataFrame:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return pd.DataFrame([dict(r) for r in rows])
    except Exception:
        conn.rollback()
        raise# Shared styling
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Core Layout Base */
    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: #f8f9ff !important;
        color: #1f2538 !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Typography & Hierarchy */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 500 !important;
        letter-spacing: -0.03em !important;
        color: #0c111d !important; /* Avoid pure black */
        margin-top: 1.5rem !important;
        margin-bottom: 0.8rem !important;
    }
    
    h1 { font-size: 2.2rem !important; }
    h2 { font-size: 1.6rem !important; }
    h3 { font-size: 1.25rem !important; }
    
    /* Sidebar Structure & Authority */
    [data-testid="stSidebar"] {
        background-color: #131b2e !important;
        color: #f8f9ff !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #e5eeff !important;
        font-family: 'Inter', sans-serif;
    }
    
    [data-testid="stSidebar"] h2 {
        font-family: 'Space Grotesk', sans-serif !important;
        color: #ffffff !important;
    }
    
    /* Precision Engineering Dashboard Cards */
    .metric-card {
        background: #ffffff;
        border: none;
        border-left: 4px solid var(--accent-color, #006a61);
        padding: 16px 20px;
        border-radius: 6px;
        box-shadow: 0 12px 40px rgba(11, 28, 48, 0.04);
        margin-bottom: 16px;
        transition: transform 120ms cubic-bezier(0.2, 0, 0, 1), box-shadow 120ms cubic-bezier(0.2, 0, 0, 1);
    }
    
    .metric-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 16px 48px rgba(11, 28, 48, 0.07);
    }
    
    .metric-title {
        font-size: 0.72rem;
        color: #4b5563;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
        margin-bottom: 4px;
    }
    
    .metric-value {
        font-size: 1.85rem;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        line-height: 1.1;
        color: #0c111d;
    }
    
    /* Tip Box (Tonal Layering, No Borders) */
    .tip-box {
        background: #eff4ff;
        border: none;
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 0.85rem;
        color: #1f2538;
        margin-bottom: 16px;
        line-height: 1.4;
    }
    
    /* High-density alternate rows for Tables */
    .stDataFrame {
        border: none !important;
    }
    
    /* Bottom-border inputs only */
    div[data-baseweb="input"] {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 2px solid #e5eeff !important;
        border-radius: 0px !important;
        color: #0c111d !important;
    }
    
    div[data-baseweb="input"]:focus-within {
        border-bottom-color: #006a61 !important;
    }
    
    /* Primary buttons matching action color */
    button[kind="primary"] {
        background-color: #006a61 !important;
        color: #ffffff !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        transition: background-color 120ms cubic-bezier(0.2, 0, 0, 1) !important;
    }
    
    button[kind="primary"]:hover {
        background-color: #004d47 !important;
    }
</style>
"""

