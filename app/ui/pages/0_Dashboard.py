import streamlit as st
import pandas as pd
from datetime import date

from app.ui.components.auth_guard import require_auth
import app.modules.analytics as analytics_srv

st.set_page_config(page_title="Dashboard - Techno Kids", layout="wide")
require_auth()

st.title("⚡ Daily Command Center")
st.markdown("Your minimalist hub for today's operations, payments, and quick registrations.")

# ── KPI Row ────────────────────────────────────────────────────────────────────
today = date.today()
sessions_today = analytics_srv.get_today_sessions(today)

total_students_today = sum(int(r.present) + int(r.absent) + int(r.unmarked) for r in sessions_today)
total_present = sum(int(r.present) for r in sessions_today)
total_unmarked = sum(int(r.unmarked) for r in sessions_today)
active_course_enrollments = analytics_srv.get_active_enrollment_count()

# Daily collection metric
collections = analytics_srv.get_revenue_by_date(today, today)
daily_collected = sum(float(r.net_revenue) for r in collections) if collections else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric(f"📅 Daily Sessions", len(sessions_today))
k2.metric("🎓 Expected Students", total_students_today)
k3.metric("✅ Present Today", total_present)
k4.metric(
    "⚠️ Unmarked",
    total_unmarked,
    delta=None if total_unmarked == 0 else f"{total_unmarked} need marking",
    delta_color="inverse",
)
k5.metric("💰 Collected Today", f"{daily_collected:,.0f} EGP")

st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_schedule, tab_finance, tab_register = st.tabs([
    "📅 Today's Schedule",
    "💳 Financial Desk",
    "⚡ Quick Registration"
])

with tab_schedule:
    st.subheader("📋 Today's Sessions & Attendance")
    if sessions_today:
        df_sessions = pd.DataFrame([r.model_dump() for r in sessions_today])
        display = df_sessions[
            ["start_time", "course_name", "group_name", "instructor_name", "total_enrolled", "present", "absent", "unmarked"]
        ].copy()
        display.columns = ["Time", "Course", "Group", "Instructor", "Enrolled", "✅ Present", "❌ Absent", "⚠️ Unmarked"]

        st.caption("Select a session to manage its attendance or details.")
        event = st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
        )

        if event.selection.rows:
            row = sessions_today[event.selection.rows[0]]
            st.session_state["selected_group_id"] = row.group_id
            st.switch_page("pages/4_Group_Management.py")
    else:
        st.info("No sessions scheduled for today.")

    unpaid_today = analytics_srv.get_today_unpaid_attendees(today)
    if unpaid_today:
        st.markdown("---")
        st.subheader("🔴 Outstanding Balances — Today's Attendees")
        st.caption("Total debt (EGP) — sum where account balance is negative (P6).")
        df_unpaid = pd.DataFrame([r.model_dump() for r in unpaid_today])[["student_name", "guardian_name", "phone_primary", "total_balance"]]
        df_unpaid.columns = ["Student", "Parent", "Phone", "Debt (EGP)"]
        df_unpaid["Debt (EGP)"] = df_unpaid["Debt (EGP)"].apply(lambda x: f"{float(x):,.0f}")
        st.dataframe(df_unpaid, use_container_width=True, hide_index=True)

with tab_finance:
    from app.ui.components.finance_overview import render_finance_overview
    from app.ui.components.finance_receipt import render_receipt_detail
    from app.ui.components.dashboard_receipts import render_receipt_browser

    if "selected_receipt_id" in st.session_state:
        render_receipt_detail(st.session_state["selected_receipt_id"])
    else:
        sub_browse, sub_record = st.tabs(["📋 Browse receipts", "➕ Record payment"])
        with sub_browse:
            render_receipt_browser()
        with sub_record:
            render_finance_overview()

with tab_register:
    from app.ui.components.quick_register import render_quick_register
    render_quick_register()
