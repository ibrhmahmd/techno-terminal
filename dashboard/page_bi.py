import streamlit as st
from datetime import date
from dashboard.config import query
from dashboard.ui_components import render_egp_metric, render_count_metric, format_egp_cols, render_download_button

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

def render_bi_page():
    st.markdown("## 📊 Overall Business Intelligence Report")
    st.markdown("Consolidated operational analysis spanning student registration, waitlists, course load, staffing, and weekly schedules.")
    st.markdown("---")

    with st.spinner("Compiling BI indicators..."):
        kpi = query_bi_kpi()

    if not kpi:
        st.warning("No BI KPI header data found. Ensure migration 076 is fully applied.")
        return

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

    st.markdown("---")

    # BI Expansion Modules
    st.markdown("### BI Expansion Modules")

    # §1 Customer Growth
    with st.expander("📈 §1 — Customer Growth", expanded=True):
        t1, t2, t3, t4 = st.tabs([
            "Monthly Trend",
            "Founding Cohort Status",
            "Demographics (Gender/Age)",
            "Completeness Detail"
        ])
        with t1:
            bi_section(
                "v_bi_new_students_monthly",
                "Monthly registration counts of new students. Key indicator of customer growth.",
                key="new_students_monthly"
            )
        with t2:
            bi_section(
                "v_bi_founding_cohort_status",
                "Distribution of current states (active, waiting, etc.) for students registered before June 2026.",
                tip="Cutoff parameter defaults to 2026-06-01. Useful for cohort retention tracking.",
                key="founding_cohort"
            )
        with t3:
            bi_section(
                "v_bi_gender_age_breakdown",
                "Aggregated metrics by gender showing student headcount and average, minimum, and maximum ages.",
                key="gender_age"
            )
        with t4:
            bi_section(
                "v_bi_demographics_completeness",
                "Analysis of missing age/gender data. A higher score guarantees high quality demographic segments.",
                key="demographics"
            )

    # §2 Waiting List & Conversion
    with st.expander("⏳ §2 — Waiting List & Conversion"):
        t1, t2, t3, t4 = st.tabs([
            "Waitlist Summary",
            "Waitlist by Join Month",
            "Wait Duration Details",
            "Conversion Rates"
        ])
        with t1:
            bi_section(
                "v_bi_waiting_list_summary",
                "Breakdown of waiting students based on whether they have prior course history or are completely new.",
                key="waiting_summary"
            )
        with t2:
            bi_section(
                "v_bi_waiting_list_by_month",
                "Current waiting list grouped by the month they registered (proxy for wait duration).",
                key="waiting_by_month"
            )
        with t3:
            bi_section(
                "v_bi_current_wait_duration",
                "Detailed wait times in days: average, median, minimum, and maximum waiting times.",
                key="wait_duration"
            )
        with t4:
            bi_section(
                "v_bi_waiting_conversion_stats",
                "Historical funnel conversion rates & speed (days elapsed) for waiting students converting to active status.",
                tip="Relies on status_change logs in student_activity_log. Returns 0 if none are tracked.",
                key="conversion_stats"
            )

    # §3 Revenue & Collections
    with st.expander("💰 §3 — Revenue & Collections"):
        t1, t2, t3, t4, t5 = st.tabs([
            "Monthly Billings",
            "Billing Ledger (Net)",
            "Completeness per Enrollment",
            "Method Distribution",
            "Avg Revenue per Student"
        ])
        with t1:
            bi_section(
                "v_bi_monthly_revenue",
                "Monthly cash flow receipts of payment transactions. Excludes refunds and soft-deleted items.",
                key="monthly_revenue"
            )
        with t2:
            bi_section(
                "v_bi_billed_vs_collected",
                "Total comparison: gross billed, discounts, net billed, actual collections, and outstanding balance.",
                key="billed_vs_collected"
            )
        with t3:
            bi_section(
                "v_bi_payment_completeness",
                "Enrollment payment states: no_charge / unpaid / partially_paid / fully_paid. Spotlights partial payers.",
                key="payment_completeness"
            )
        with t4:
            bi_section(
                "v_bi_payment_method_mix",
                "Billing methods breakdowns (e.g. Cash, Card, Bank Transfer) with contribution percentages.",
                key="payment_methods"
            )
        with t5:
            bi_section(
                "v_bi_avg_revenue_per_student",
                "Average lifetime revenue collected per paying student.",
                key="avg_revenue"
            )

    # §4 Course Performance
    with st.expander("📚 §4 — Course Performance"):
        t1, t2 = st.tabs(["Course Profitability", "Exceeded Capacity alerts"])
        with t1:
            bi_section(
                "v_bi_course_performance",
                "Performance by course title: active classes, distinct student headcount, and total net revenue.",
                key="course_perf"
            )
        with t2:
            bi_section(
                "v_bi_groups_over_capacity",
                "List of active groups exceeding their max_capacity limits. Needs quick operational re-routing.",
                key="over_capacity"
            )

    # §5 Staffing & Instructor Cost
    with st.expander("👷 §5 — Staffing & Instructor Cost"):
        t1, t2, t3, t4 = st.tabs([
            "Instructor Load",
            "Revenue Share Cost",
            "Idle Staff exceptions",
            "Headcount Register"
        ])
        with t1:
            bi_section(
                "v_bi_instructor_load",
                "Current classes taught and total active student headcount per instructor.",
                key="instructor_load"
            )
        with t2:
            bi_section(
                "v_bi_contract_instructor_cost",
                "Revenue-share estimates for contract instructors based on course pricing and contract rate.",
                tip="Calculated using employees.contract_percentage, falling back to 25% if null.",
                key="contract_cost"
            )
        with t3:
            bi_section(
                "v_bi_contract_instructors_idle",
                "Contract staff active but with no current teaching assignments. Spotlights available capacity.",
                key="idle_instructors"
            )
        with t4:
            bi_section(
                "v_bi_headcount_by_type",
                "Headcount and total monthly fixed salary obligation by employee category (e.g. full_time, part_time).",
                key="headcount"
            )

    # §7 Attendance & Lifecycle
    with st.expander("📋 §7 — Attendance & Enrollment Lifecycle"):
        t1, t2 = st.tabs(["Attendance Rates", "Enrollment States"])
        with t1:
            bi_section(
                "v_bi_attendance_rate",
                "Attendance status distribution (e.g. Present, Absent, Excused) showing contribution rates.",
                key="attendance_rate"
            )
        with t2:
            bi_section(
                "v_bi_enrollment_status",
                "Student status states across enrollments: active / dropped / transferred / completed.",
                key="enrollment_status"
            )

    # §8 Weekly Schedule
    with st.expander("🗓️ §8 — Weekly Schedule"):
        bi_section(
            "v_bi_weekly_schedule",
            "Total weekly active groups categorized by session slot: Afternoon (<17:00) vs Evening (>=17:00).",
            key="weekly_schedule"
        )
