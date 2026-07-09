"""
Techno Terminal — Finance & Audit Dashboard
Main entry point. Orchestrates sidebar sub-navigation and page routing.

Run:   streamlit run audit_dashboard.py
"""

import streamlit as st
from datetime import datetime

# Configure page metadata
st.set_page_config(
    page_title="Techno Terminal — Finance & Audit Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import sub-modules
from dashboard.config import CUSTOM_CSS, SEVERITY_COLOR
from dashboard.page_audit import render_audit_page
from dashboard.page_finance import render_finance_page
from dashboard.page_bi import render_bi_page

# Inject styles
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar Navigation & General Controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; padding: 10px 0 20px 0;">
            <h2 style="margin: 0; color: #FFF; font-weight: 700; letter-spacing: -0.03em;">🚀 TECHNO KIDS</h2>
            <p style="margin: 0; font-size: 0.8rem; color: #8E92B2; text-transform: uppercase; letter-spacing: 0.1em;">Management Portal</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("---")

    # 1. Main Navigation Category Selector
    section = st.radio(
        "Navigation Section",
        ["🔍 Integrity Audit", "💰 Finance Registers", "📊 BI Reports"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # 2. Sub-Navigation View/Page Selector
    st.markdown("### View Register")
    
    if section == "🔍 Integrity Audit":
        audit_options = {
            "Overview": "Overview Dashboard",
            "A": "A: Zero-Charge Active Enrollments",
            "B": "B: Overpaid Enrollments (Credits)",
            "C": "C: Orphaned Payments (Unlinked)",
            "D": "D: Duplicate Active Enrollments",
            "E": "E: Active Enrollments on Dead Groups",
            "F": "F: Dropped/Transferred Unrefunded",
            "G": "G: Level Mismatch (No level row)",
            "H": "H: Active Payments for Deleted Students",
            "I": "I: Full or Over-Discounts (>=100%)"
        }
        active_sub_label = st.selectbox(
            "Select Scenario",
            options=list(audit_options.values()),
            label_visibility="collapsed"
        )
        # Find key from value
        active_page = next(k for k, v in audit_options.items() if v == active_sub_label)
        
        # Scenario filters
        st.markdown("---")
        st.markdown("### Filter Settings")
        start_date = st.date_input(
            "Exclude historical data before",
            value=None,
            help="Useful to exclude June 2026 bulk-import records.",
        )
        
        st.markdown("---")
        st.markdown("**Severity Level Reference**")
        for sev, color in SEVERITY_COLOR.items():
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
                f'<div style="width:10px;height:10px;background:{color};border-radius:50%;box-shadow:0 0 6px {color}aa"></div>'
                f'<span style="font-size:0.8rem;color:#B4B9DC;font-weight:500">{sev}</span></div>',
                unsafe_allow_html=True,
            )
            
    elif section == "💰 Finance Registers":
        finance_options = {
            "Overview": "Overview Dashboard",
            "outstanding": "💳 Outstanding Balances (AR)",
            "monthly_revenue": "📈 Monthly Revenue",
            "by_course": "📚 Revenue by Course",
            "collection_rate": "📉 Collection Rate by Group",
            "payment_methods": "💰 Payment Methods",
            "contract_costs": "👷 Contract Instructor Costs",
            "parttime_alloc": "🗓️ Part-Time Allocation",
            "payroll_vs_revenue": "📊 Payroll vs Revenue",
            "discounts": "🏷️ Discount Impact",
            "high_risk": "⚠️ High-Risk Balances (AR Aging)",
            "group_summary": "🏫 Group Revenue Summary",
            "waiting_potential": "⏳ Waiting List Potential"
        }
        active_sub_label = st.selectbox(
            "Select Register",
            options=list(finance_options.values()),
            label_visibility="collapsed"
        )
        active_page = next(k for k, v in finance_options.items() if v == active_sub_label)
        start_date = None
        
    else:  # section == "📊 BI Reports"
        bi_options = {
            "Overview": "Overview Dashboard",
            "new_students_monthly": "📈 §1.1 — New Students / Month",
            "founding_cohort": "👥 §1.2 — Founding Cohort Status",
            "gender_age": "🧬 §1.3 — Gender & Age",
            "demographics": "📋 §1.4 — Demographics Completeness",
            "waiting_summary": "⏳ §2.1 — Waitlist Summary",
            "waiting_by_month": "📅 §2.2 — Waitlist by Join Month",
            "wait_duration": "⏱️ §2.3 — Current Wait Duration",
            "conversion_stats": "🔄 §2.4 — Conversion Rates",
            "monthly_revenue": "💵 §3.1 — Monthly Revenue",
            "billed_vs_collected": "⚖️ §3.2 — Billed vs Collected",
            "payment_completeness": "🗂️ §3.3 — Payment Completeness",
            "payment_methods": "💳 §3.4 — Payment Method Mix",
            "avg_revenue": "💡 §3.5 — Average Revenue per Student",
            "course_perf": "📚 §4.1 — Course Performance",
            "over_capacity": "🚨 §4.2 — Groups Over Capacity",
            "instructor_load": "📋 §5.1 — Instructor Load",
            "contract_cost": "💰 §5.2 — Contract Cost",
            "idle_instructors": "⚠️ §5.3 — Idle Instructors",
            "headcount": "👥 §5.4 — Headcount",
            "attendance_rate": "📅 §7.1 — Attendance Rates",
            "enrollment_status": "📋 §7.2 — Enrollment Lifecycle Status",
            "weekly_schedule": "🗓️ §8.0 — Weekly Schedule"
        }
        active_sub_label = st.selectbox(
            "Select Report",
            options=list(bi_options.values()),
            label_visibility="collapsed"
        )
        active_page = next(k for k, v in bi_options.items() if v == active_sub_label)
        start_date = None

    # Global actions & cache controls
    st.markdown("---")
    st.markdown("### System Diagnostics")
    refresh = st.button("🔄 Reload Local Cache", use_container_width=True)
    if refresh:
        st.cache_resource.clear()
        st.rerun()

    st.markdown(
        f'<div style="color:#A9A9A9;font-size:0.72rem;margin-top:12px;text-align:center">'
        f'Last loaded: {datetime.now().strftime("%I:%M:%S %p")}</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Router & Main Window Rendering
# ---------------------------------------------------------------------------
if section == "🔍 Integrity Audit":
    render_audit_page(start_date, active_page)
elif section == "💰 Finance Registers":
    render_finance_page(active_page)
else:  # section == "📊 BI Reports"
    render_bi_page(active_page)
