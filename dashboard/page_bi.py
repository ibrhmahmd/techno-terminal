import streamlit as st
from datetime import date
from dashboard.config import query
from dashboard.ui_components import render_egp_metric, render_count_metric, format_egp_cols, render_download_button

# Config mappings for BI Pages
BI_PAGES = {
    "new_students_monthly": {
        "view": "v_bi_new_students_monthly",
        "description": "Monthly registration counts of new students. Key indicator of customer growth.",
        "label": "📈 §1.1 — New Students / Month",
        "tip": ""
    },
    "founding_cohort": {
        "view": "v_bi_founding_cohort_status",
        "description": "Distribution of current states (active, waiting, etc.) for students registered before June 2026.",
        "label": "👥 §1.2 — Founding Cohort Status",
        "tip": "Cutoff parameter defaults to 2026-06-01. Useful for cohort retention tracking."
    },
    "gender_age": {
        "view": "v_bi_gender_age_breakdown",
        "description": "Aggregated metrics by gender showing student headcount and average, minimum, and maximum ages.",
        "label": "🧬 §1.3 — Gender & Age",
        "tip": ""
    },
    "demographics": {
        "view": "v_bi_demographics_completeness",
        "description": "Analysis of missing age/gender data. A higher score guarantees high quality demographic segments.",
        "label": "📋 §1.4 — Demographics Completeness",
        "tip": ""
    },
    "waiting_summary": {
        "view": "v_bi_waiting_list_summary",
        "description": "Breakdown of waiting students based on whether they have prior course history or are completely new.",
        "label": "⏳ §2.1 — Waitlist Summary",
        "tip": "Conversion rate = conversions / (conversions + still_waiting)."
    },
    "waiting_by_month": {
        "view": "v_bi_waiting_list_by_month",
        "description": "Current waiting list grouped by the month they registered (proxy for wait duration).",
        "label": "📅 §2.2 — Waitlist by Join Month",
        "tip": ""
    },
    "wait_duration": {
        "view": "v_bi_current_wait_duration",
        "description": "Detailed wait times in days: average, median, minimum, and maximum waiting times.",
        "label": "⏱️ §2.3 — Current Wait Duration",
        "tip": ""
    },
    "conversion_stats": {
        "view": "v_bi_waiting_conversion_stats",
        "description": "Historical funnel conversion rates & speed (days elapsed) for waiting students converting to active status.",
        "label": "🔄 §2.4 — Conversion Rates",
        "tip": "Relies on status_change logs in student_activity_log. Returns 0 if none are tracked."
    },
    "monthly_revenue": {
        "view": "v_bi_monthly_revenue",
        "description": "Monthly cash flow receipts of payment transactions. Excludes refunds and soft-deleted items.",
        "label": "💵 §3.1 — Monthly Revenue",
        "tip": ""
    },
    "billed_vs_collected": {
        "view": "v_bi_billed_vs_collected",
        "description": "Total comparison: gross billed, discounts, net billed, actual collections, and outstanding balance.",
        "label": "⚖️ §3.2 — Billed vs Collected",
        "tip": ""
    },
    "payment_completeness": {
        "view": "v_bi_payment_completeness",
        "description": "Enrollment payment states: no_charge / unpaid / partially_paid / fully_paid. Spotlights partial payers.",
        "label": "🗂️ §3.3 — Payment Completeness",
        "tip": ""
    },
    "payment_methods": {
        "view": "v_bi_payment_method_mix",
        "description": "Billing methods breakdowns (e.g. Cash, Card, Bank Transfer) with contribution percentages.",
        "label": "💳 §3.4 — Payment Method Mix",
        "tip": ""
    },
    "avg_revenue": {
        "view": "v_bi_avg_revenue_per_student",
        "description": "Average lifetime revenue collected per paying student.",
        "label": "💡 §3.5 — Average Revenue",
        "tip": ""
    },
    "course_perf": {
        "view": "v_bi_course_performance",
        "description": "Performance by course title: active classes, distinct student headcount, and total net revenue.",
        "label": "📚 §4.1 — Course Performance",
        "tip": "Use as a treemap or ranked table in your BI tool."
    },
    "over_capacity": {
        "view": "v_bi_groups_over_capacity",
        "description": "List of active groups exceeding their max_capacity limits. Needs quick operational re-routing.",
        "label": "🚨 §4.2 — Groups Over Capacity",
        "tip": "Run as a scheduled check — should trigger an ops notification automatically."
    },
    "instructor_load": {
        "view": "v_bi_instructor_load",
        "description": "Current classes taught and total active student headcount per instructor.",
        "label": "📋 §5.1 — Instructor Load",
        "tip": ""
    },
    "contract_cost": {
        "view": "v_bi_contract_instructor_cost",
        "description": "Revenue-share estimates for contract instructors based on course pricing and contract rate.",
        "label": "💰 §5.2 — Contract Cost",
        "tip": "Calculated using employees.contract_percentage, falling back to 25% if null."
    },
    "idle_instructors": {
        "view": "v_bi_contract_instructors_idle",
        "description": "Contract staff active but with no current teaching assignments. Spotlights available capacity.",
        "label": "⚠️ §5.3 — Idle Instructors",
        "tip": ""
    },
    "headcount": {
        "view": "v_bi_headcount_by_type",
        "description": "Headcount and total monthly fixed salary obligation by employee category (e.g. full_time, part_time).",
        "label": "👥 §5.4 — Headcount",
        "tip": ""
    },
    "attendance_rate": {
        "view": "v_bi_attendance_rate",
        "description": "Attendance status distribution (e.g. Present, Absent, Excused) showing contribution rates.",
        "label": "📅 §7.1 — Attendance Rates",
        "tip": ""
    },
    "enrollment_status": {
        "view": "v_bi_enrollment_status",
        "description": "Student status states across enrollments: active / dropped / transferred / completed.",
        "label": "📋 §7.2 — Enrollment Lifecycle Status",
        "tip": ""
    },
    "weekly_schedule": {
        "view": "v_bi_weekly_schedule",
        "description": "Total weekly active groups categorized by session slot: Afternoon (<17:00) vs Evening (>=17:00).",
        "label": "🗓️ §8.0 — Weekly Schedule",
        "tip": "The 17:00 afternoon/evening cutoff should be confirmed as a business rule before wiring into a live dashboard."
    }
}

def query_bi_kpi() -> dict:
    try:
        df = query("SELECT * FROM v_bi_kpi_header")
        if df.empty:
            return {}
        return df.iloc[0].to_dict()
    except Exception as e:
        st.error(f"Failed to load BI KPIs: {e}")
        return {}

def bi_section(view: str, description: str, tip: str = "", key: str = ""):
    st.markdown(f"**{description}**")
    if tip:
        st.markdown(
            f'<div class="tip-box">💡 <strong>BI Tip:</strong> {tip}</div>',
            unsafe_allow_html=True,
        )
    with st.spinner(f"Loading {view}..."):
        try:
            df = query(f"SELECT * FROM {view}")
        except Exception as e:
            st.error(f"Query failed for `{view}`: {e}")
            return
            
    if df.empty:
        st.info("No data returned.")
        return
        
    st.markdown(f"**Records found: {len(df)}**")
    st.dataframe(format_egp_cols(df), use_container_width=True, hide_index=True)
    
    col_dl, _ = st.columns([1, 3])
    with col_dl:
        render_download_button(df, f"bi_{key or view}", "Export Report to CSV")

def render_bi_page(active_page: str):
    st.markdown("## 📊 Overall Business Intelligence Report")
    st.markdown("Consolidated operational analysis spanning student registration, waitlists, course load, staffing, and weekly schedules.")
    st.markdown("---")

    with st.spinner("Compiling BI indicators..."):
        kpi = query_bi_kpi()

    if not kpi:
        st.warning("No BI KPI header data found. Ensure migration 076 is fully applied.")
        return

    # Overview Page
    if active_page == "Overview":
        # BI KPI Header Summary
        st.markdown("### Strategic Performance Indicators (KPIs)")
        k1, k2, k3, k4 = st.columns(4)
        render_count_metric(k1, "Enrolled Active Students", kpi.get("active_students"), "🟢", "#4CAF50")
        render_count_metric(k2, "Waiting List Students", kpi.get("waiting_students"), "⏳", "#FFA500")
        render_count_metric(k3, "New Enrolled (MTD)", kpi.get("new_students_this_month"), "✨", "#4B9EFF")
        render_count_metric(k4, "Active Cohort Groups", kpi.get("active_groups"), "🏫", "#9B59B6")

        k5, k6, k7, k8 = st.columns(4)
        render_egp_metric(k5, "Revenue (MTD)", kpi.get("revenue_this_month"), "📅", "#4CAF50")
        render_egp_metric(k6, "Total All-Time Revenue", kpi.get("revenue_all_time"), "💵", "#4B9EFF")
        render_egp_metric(k7, "Avg Lifetime Rev / Student", kpi.get("avg_revenue_per_student"), "💡", "#E67E22")
        
        # Collection rate gauge color logic
        col_rate = kpi.get("collection_rate_pct")
        try:
            rate_val = float(col_rate) if col_rate is not None else 0.0
        except (ValueError, TypeError):
            rate_val = 0.0
        rate_color = "#4CAF50" if rate_val >= 80 else "#FFA500" if rate_val >= 60 else "#FF4B4B"
        
        k8.markdown(
            f"""
            <div class="metric-card" style="--accent-color: {rate_color}">
                <div class="metric-title">📊 Total Collection Rate</div>
                <div class="metric-value" style="color: {rate_color}">{col_rate}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Operational warning alert bar
        over_capacity = kpi.get("groups_over_capacity", 0)
        idle_instructors = kpi.get("idle_contract_instructors", 0)
        demo_pct = kpi.get("demographics_completeness_pct")
        
        if over_capacity or idle_instructors or demo_pct:
            st.markdown("### Operational Alerts & Completeness")
            a1, a2, a3 = st.columns(3)
            render_count_metric(a1, "Groups Exceeding Capacity", over_capacity, "🚨", "#FF4B4B" if over_capacity > 0 else "#4CAF50")
            render_count_metric(a2, "Unallocated/Idle Contract staff", idle_instructors, "⚠️", "#FFA500" if idle_instructors > 0 else "#4CAF50")
            
            try:
                demo_val = float(demo_pct) if demo_pct is not None else 0.0
            except (ValueError, TypeError):
                demo_val = 0.0
            demo_color = "#4CAF50" if demo_val >= 80 else "#FFA500"
            
            a3.markdown(
                f"""
                <div class="metric-card" style="--accent-color: {demo_color}">
                    <div class="metric-title">🧬 Demographics Data Completeness</div>
                    <div class="metric-value" style="color: {demo_color}">{demo_pct}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Specific Report Page
    else:
        page_info = BI_PAGES.get(active_page)
        if not page_info:
            st.error(f"Report view {active_page} not found.")
            return

        st.markdown(f"### {page_info['label']}")
        bi_section(
            page_info["view"],
            page_info["description"],
            tip=page_info.get("tip", ""),
            key=active_page
        )
