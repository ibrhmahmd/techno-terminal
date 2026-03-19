import streamlit as st
import pandas as pd
from datetime import date, timedelta
from calendar import monthrange

from app.ui.components.auth_guard import require_auth
from app.modules.analytics import analytics_service as analytics_srv
from app.modules.academics import academics_service as acad_srv

st.set_page_config(page_title="Reports - Techno Kids", layout="wide")
require_auth()

st.title("📊 Reports & Analytics")
st.divider()

tab_fin, tab_acad, tab_comp, tab_heatmap, tab_bi = st.tabs(
    ["💰 Financial", "🎓 Academic", "🏆 Competitions", "📋 Attendance Heatmap", "📈 Business Intelligence"]
)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — FINANCIAL
# ─────────────────────────────────────────────────────────────────────────────
with tab_fin:
    today = date.today()
    first_this_month = today.replace(day=1)
    last_month_end = first_this_month - timedelta(days=1)
    first_last_month = last_month_end.replace(day=1)

    preset = st.radio(
        "Date Range",
        ["Today", "This Month", "Last Month", "Custom"],
        horizontal=True,
        key="fin_preset",
    )

    if preset == "Today":
        fin_start, fin_end = today, today
    elif preset == "This Month":
        fin_start, fin_end = first_this_month, today
    elif preset == "Last Month":
        fin_start, fin_end = first_last_month, last_month_end
    else:
        c1, c2 = st.columns(2)
        fin_start = c1.date_input("From", value=first_this_month, key="fin_from")
        fin_end = c2.date_input("To", value=today, key="fin_to")

    st.markdown(f"**Period:** {fin_start} → {fin_end}")
    st.divider()

    rev_by_method = analytics_srv.get_revenue_by_method(fin_start, fin_end)
    rev_by_date = analytics_srv.get_revenue_by_date(fin_start, fin_end)
    outstanding = analytics_srv.get_outstanding_by_group()
    debtors = analytics_srv.get_top_debtors(limit=15)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("💳 Revenue by Payment Method")
        if rev_by_method:
            df_m = pd.DataFrame(rev_by_method)
            df_m["net_revenue"] = df_m["net_revenue"].apply(float)
            total = df_m["net_revenue"].sum()
            st.metric("Total Collected", f"{total:,.0f} EGP")
            chart = df_m.set_index("payment_method")[["net_revenue"]]
            chart.index.name = "Method"
            chart.columns = ["Revenue (EGP)"]
            st.bar_chart(chart)
            st.dataframe(
                df_m.rename(
                    columns={
                        "payment_method": "Method",
                        "net_revenue": "Revenue (EGP)",
                        "receipt_count": "Receipts",
                    }
                ),
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("No revenue data for this period.")

    with col2:
        st.subheader("📈 Daily Revenue Trend")
        if rev_by_date:
            df_d = pd.DataFrame(rev_by_date)
            df_d["net_revenue"] = df_d["net_revenue"].apply(float)
            df_d = df_d.set_index("day")
            df_d.columns = ["Revenue (EGP)"]
            df_d.index.name = "Date"
            st.line_chart(df_d)
        else:
            st.info("No daily data available.")

    st.divider()
    st.subheader("🔴 Outstanding Balances by Group")
    if outstanding:
        df_out = pd.DataFrame(outstanding)
        df_out["total_outstanding"] = df_out["total_outstanding"].apply(float)
        df_out = df_out.rename(
            columns={
                "group_name": "Group",
                "course_name": "Course",
                "students_with_balance": "Students Owing",
                "total_outstanding": "Total Outstanding (EGP)",
            }
        ).drop(columns=["group_id"])
        st.dataframe(df_out, hide_index=True, use_container_width=True)

        csv = df_out.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Outstanding Balances CSV",
            csv,
            "outstanding_balances.csv",
            "text/csv",
        )
    else:
        st.success("✅ No outstanding balances!")

    st.divider()
    st.subheader("👤 Top Debtors")
    if debtors:
        df_debt = pd.DataFrame(debtors)
        df_debt["total_outstanding"] = df_debt["total_outstanding"].apply(float)
        df_debt = df_debt.rename(
            columns={
                "student_name": "Student",
                "guardian_name": "Parent",
                "phone_primary": "Phone",
                "total_outstanding": "Owed (EGP)",
            }
        ).drop(columns=["student_id"])
        event_debt = st.dataframe(
            df_debt,
            hide_index=True,
            use_container_width=True,
            selection_mode="single-row",
            on_select="rerun",
        )
        if event_debt.selection.rows:
            sel_idx = event_debt.selection.rows[0]
            st.session_state["nav_target_student_id"] = debtors[sel_idx]["student_id"]
            st.switch_page("pages/1_Directory.py")
    else:
        st.info("No debtors found.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — ACADEMIC (Group Roster)
# ─────────────────────────────────────────────────────────────────────────────
with tab_acad:
    st.subheader("🎓 Group Roster Report")
    st.caption(
        "Select a group and level to see the full student roster with attendance % and balance."
    )

    show_inactive = st.checkbox("Show inactive/archived groups", key="acad_inactive")
    groups = acad_srv.get_all_active_groups(include_inactive=show_inactive)
    if not groups:
        st.info("No groups found.")
    else:
        sel_group = st.selectbox(
            "Select Group", 
            options=groups, 
            format_func=lambda g: f"{g.name} (ID:{g.id})",
            key="acad_group"
        )

        levels = list(range(1, (sel_group.level_number or 1) + 1))
        sel_level = st.selectbox(
            "Select Level", levels, index=len(levels) - 1, key="acad_level"
        )

        roster = analytics_srv.get_group_roster(sel_group.id, sel_level)
        if roster:
            df_roster = pd.DataFrame(roster)
            df_roster["balance"] = df_roster["balance"].apply(float)
            df_roster["attendance_pct"] = df_roster["attendance_pct"].apply(float)
            df_roster = df_roster.rename(
                columns={
                    "student_name": "Student",
                    "enrollment_status": "Status",
                    "balance": "Balance (EGP)",
                    "sessions_attended": "Present",
                    "sessions_missed": "Absent",
                    "total_sessions": "Total Sessions",
                    "attendance_pct": "Attendance %",
                }
            ).drop(columns=["student_id", "enrollment_id"], errors="ignore")

            st.dataframe(df_roster, hide_index=True, use_container_width=True)

            csv = df_roster.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download Roster CSV",
                csv,
                f"roster_{sel_group.id}_level{sel_level}.csv",
                "text/csv",
            )
        else:
            st.info("No active enrollments found for this group and level.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — COMPETITIONS
# ─────────────────────────────────────────────────────────────────────────────
with tab_comp:
    st.subheader("🏆 Competition Fee Summary")
    fee_summary = analytics_srv.get_competition_fee_summary()
    if fee_summary:
        df_comp = pd.DataFrame(fee_summary)
        df_comp["fees_collected"] = df_comp["fees_collected"].apply(float)
        df_comp["fees_outstanding"] = df_comp["fees_outstanding"].apply(float)
        df_comp["competition_date"] = df_comp["competition_date"].astype(str)

        total_collected = df_comp["fees_collected"].sum()
        total_outstanding = df_comp["fees_outstanding"].sum()

        k1, k2, k3 = st.columns(3)
        k1.metric("Total Competitions", len(df_comp))
        k2.metric("💰 Fees Collected", f"{total_collected:,.0f} EGP")
        k3.metric(
            "⚠️ Fees Outstanding",
            f"{total_outstanding:,.0f} EGP",
            delta=f"-{total_outstanding:,.0f} EGP" if total_outstanding > 0 else None,
            delta_color="inverse",
        )

        st.divider()
        df_display = df_comp.rename(
            columns={
                "competition_name": "Competition",
                "competition_date": "Date",
                "team_count": "Teams",
                "member_count": "Members",
                "fees_collected": "Collected (EGP)",
                "fees_outstanding": "Outstanding (EGP)",
            }
        ).drop(columns=["competition_id"])

        st.dataframe(df_display, hide_index=True, use_container_width=True)

        csv = df_display.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, "competition_fees.csv", "text/csv")
    else:
        st.info("No competitions found.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — ATTENDANCE HEATMAP
# ─────────────────────────────────────────────────────────────────────────────
with tab_heatmap:
    st.subheader("📋 Attendance Heatmap")
    st.caption("See each student's attendance per session in one view.")

    show_inactive_h = st.checkbox("Show inactive/archived groups", key="heat_inactive")
    groups_h = acad_srv.get_all_active_groups(include_inactive=show_inactive_h)
    if not groups_h:
        st.info("No groups found.")
    else:
        sel_group_h = st.selectbox(
            "Select Group", 
            options=groups_h, 
            format_func=lambda g: f"{g.name} (ID:{g.id})",
            key="heat_group"
        )

        levels_h = list(range(1, (sel_group_h.level_number or 1) + 1))
        sel_level_h = st.selectbox(
            "Select Level", levels_h, index=len(levels_h) - 1, key="heat_level"
        )

        heat_data = analytics_srv.get_attendance_heatmap(sel_group_h.id, sel_level_h)
        if heat_data:
            df_heat = pd.DataFrame(heat_data)

            # Pivot: rows = student, columns = session_number + date
            df_heat["session_label"] = df_heat.apply(
                lambda r: f"S{int(r['session_number'])}\n{str(r['session_date'])[:10]}",
                axis=1,
            )

            STATUS_EMOJI = {
                "present": "✅",
                "absent": "❌",
                "late": "🕐",
                "unmarked": "—",
            }
            df_heat["emoji"] = df_heat["status"].map(STATUS_EMOJI).fillna("—")

            pivot = df_heat.pivot_table(
                index="student_name",
                columns="session_label",
                values="emoji",
                aggfunc="first",
            )
            pivot.index.name = "Student"
            pivot.columns.name = None

            st.dataframe(pivot, use_container_width=True)

            # CSV export uses raw status not emoji
            pivot_raw = df_heat.pivot_table(
                index="student_name",
                columns="session_label",
                values="status",
                aggfunc="first",
            )
            csv = pivot_raw.to_csv().encode("utf-8")
            st.download_button(
                "⬇️ Download Heatmap CSV",
                csv,
                f"attendance_heatmap_{sel_group_h.id}_level{sel_level_h}.csv",
                "text/csv",
            )
            st.info("No sessions or enrollments found for this group and level.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — BUSINESS INTELLIGENCE
# ─────────────────────────────────────────────────────────────────────────────
with tab_bi:
    st.subheader("📈 Business Intelligence")
    st.caption("Deep analytics on growth, retention, and instructor performance.")

    bi_col1, bi_col2 = st.columns(2, gap="large")

    with bi_col1:
        st.markdown("#### 🌱 Enrollment Growth")
        days = st.slider("Timeframe (Days)", min_value=7, max_value=365, value=30, step=7)
        cutoff = date.today() - timedelta(days=days)
        growth_data = analytics_srv.get_new_enrollments_trend(cutoff)
        
        if growth_data:
            df_growth = pd.DataFrame(growth_data)
            df_growth = df_growth.set_index("day")
            st.bar_chart(df_growth)
            
            total_new = df_growth["new_enrollments"].sum()
            st.metric(f"New Enrollments (Last {days} days)", total_new)
        else:
            st.info("No new enrollments in this timeframe.")

    with bi_col2:
        st.markdown("#### 🎯 Course Retention rates")
        retention = analytics_srv.get_retention_metrics()
        
        if retention:
            df_ret = pd.DataFrame(retention)
            df_ret["retention_rate"] = df_ret.apply(
                lambda row: (row["active_count"] / row["total_enrollments"]) * 100 if row["total_enrollments"] > 0 else 0, 
                axis=1
            )
            df_ret = df_ret.sort_values(by="retention_rate", ascending=False)
            
            st.dataframe(
                df_ret[["course_name", "active_count", "dropped_count", "retention_rate"]].rename(
                    columns={
                        "course_name": "Course",
                        "active_count": "Active",
                        "dropped_count": "Dropped",
                        "retention_rate": "Retention (%)"
                    }
                ).style.format({"Retention (%)": "{:.1f}%"}),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No retention data.")

    st.divider()
    
    st.markdown("#### 👨‍🏫 Instructor Performance Metrics")
    perf = analytics_srv.get_instructor_performance()
    
    if perf:
        df_perf = pd.DataFrame(perf)
        df_perf = df_perf.rename(
            columns={
                "instructor_name": "Instructor",
                "active_groups": "Active Groups",
                "active_students": "Total Active Students"
            }
        )
        st.dataframe(df_perf, hide_index=True, use_container_width=True)
    else:
        st.info("No active instructors data.")
