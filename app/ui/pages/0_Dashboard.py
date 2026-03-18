import streamlit as st
import pandas as pd
from datetime import date, timedelta

from app.ui.components.auth_guard import require_auth
from app.modules.analytics import service as analytics_srv

st.set_page_config(page_title="Dashboard - Techno Kids", layout="wide")
require_auth()

today = date.today()
month_start = today.replace(day=1)

col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.title("📊 Operations Dashboard")
with col_t2:
    selected_date = st.date_input("Filter Date", max_value=date.today())

st.caption(f"Showing operations for **{selected_date.strftime('%A, %d %B %Y')}**")
st.divider()

# ── Load data ──────────────────────────────────────────────────────────────────
sessions_today = analytics_srv.get_today_sessions(selected_date)
unpaid_today = analytics_srv.get_today_unpaid_attendees(selected_date)
revenue_mtd = analytics_srv.get_revenue_by_date(month_start, today)
revenue_by_method = analytics_srv.get_revenue_by_method(month_start, today)
active_course_enrollments = analytics_srv.get_active_enrollment_count()

mtd_total = sum(float(r["net_revenue"]) for r in revenue_mtd)
total_students_today = sum(
    int(r["present"]) + int(r["absent"]) + int(r["unmarked"]) for r in sessions_today
)
total_present = sum(int(r["present"]) for r in sessions_today)
total_unmarked = sum(int(r["unmarked"]) for r in sessions_today)

# ── KPI Row ────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric(f"📅 Daily Sessions", len(sessions_today))
k2.metric("🎓 Expected Students", total_students_today)
k3.metric("✅ Present", total_present)
k4.metric(
    "⚠️ Unmarked",
    total_unmarked,
    delta=None if total_unmarked == 0 else f"{total_unmarked} need marking",
    delta_color="inverse",
)
k5.metric("📈 Active Enrollments", active_course_enrollments)
k6.metric("💰 MTD Revenue", f"{mtd_total:,.0f} EGP")

st.divider()

# ── Main content ───────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    st.subheader("📋 Today's Sessions")
    if sessions_today:
        df_sessions = pd.DataFrame(sessions_today)

        # Clean display columns
        display = df_sessions[
            [
                "start_time",
                "course_name",
                "group_name",
                "instructor_name",
                "total_enrolled",
                "present",
                "absent",
                "unmarked",
            ]
        ].copy()
        display.columns = [
            "Time",
            "Course",
            "Group",
            "Instructor",
            "Enrolled",
            "✅ Present",
            "❌ Absent",
            "⚠️ Unmarked",
        ]

        event = st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
        )

        if event.selection.rows:
            row = sessions_today[event.selection.rows[0]]
            st.session_state["nav_target_group_id"] = row["group_id"]
            st.switch_page("pages/4_Group_Management.py")
    else:
        st.info("No sessions scheduled for the selected date.")

    if unpaid_today:
        st.markdown("---")
        st.subheader("🔴 Outstanding Balances — Today's Attendees")
        df_unpaid = pd.DataFrame(unpaid_today)[
            ["student_name", "guardian_name", "phone_primary", "total_balance"]
        ]
        df_unpaid.columns = ["Student", "Parent", "Phone", "Balance (EGP)"]
        df_unpaid["Balance (EGP)"] = df_unpaid["Balance (EGP)"].apply(
            lambda x: f"{float(x):,.0f}"
        )
        st.dataframe(df_unpaid, use_container_width=True, hide_index=True)

with col_right:
    st.subheader("💳 MTD Revenue by Method")
    if revenue_by_method:
        df_method = pd.DataFrame(revenue_by_method)
        df_method["net_revenue"] = df_method["net_revenue"].apply(float)
        df_method = df_method.rename(
            columns={
                "payment_method": "Method",
                "net_revenue": "Net Revenue (EGP)",
                "receipt_count": "Receipts",
            }
        )
        st.dataframe(df_method, use_container_width=True, hide_index=True)

        # Bar chart
        chart_data = df_method.set_index("Method")[["Net Revenue (EGP)"]]
        st.bar_chart(chart_data)
    else:
        st.info("No payments received this month yet.")

    st.markdown("---")
    st.subheader("📈 Revenue Trend This Month")
    if revenue_mtd:
        df_trend = pd.DataFrame(revenue_mtd)
        df_trend["net_revenue"] = df_trend["net_revenue"].apply(float)
        df_trend = df_trend.rename(
            columns={"day": "Date", "net_revenue": "Revenue (EGP)"}
        )
        df_trend = df_trend.set_index("Date")
        st.line_chart(df_trend)
    else:
        st.info("No revenue data yet this month.")
