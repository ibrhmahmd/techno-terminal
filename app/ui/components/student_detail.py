import streamlit as st
import pandas as pd
from app.modules.crm import crm_service
from app.modules.enrollments import get_student_enrollments
from app.modules.attendance import get_attendance_summary
from app.modules.academics import get_group_by_id
from app.modules.finance import finance_service as fin_srv
from app.modules.competitions import team_service as comp_srv
from app.db.connection import get_session


def render_student_detail(student_id: int):
    student = crm_service.get_student_by_id(student_id)

    if not student:
        st.error("Student not found.")
        if st.button("⬅️ Back"):
            del st.session_state["nav_target_student_id"]
            st.rerun()
        return

    # Header section
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            del st.session_state["nav_target_student_id"]
            st.rerun()
    with col2:
        status_icon = "🟢" if student.is_active else "🔴"
        st.subheader(f"Profile: {student.full_name} {status_icon}")

    # Profile Bar
    c_age, c_gen, c_ph = st.columns(3)
    c_age.markdown(f"**Date of Birth:** {student.date_of_birth}")
    c_gen.markdown(f"**Gender:** {student.gender.capitalize()}")
    c_ph.markdown(f"**Phone:** {student.phone or 'N/A'}")

    if student.notes:
        st.info(f"**Notes:** {student.notes}")

    from app.ui.components.forms.edit_student_form import render_edit_student_form
    render_edit_student_form(student)

    st.divider()

    # 1. Parent Info
    st.markdown("#### Parent/Parent Details")

    parents = crm_service.get_student_guardians(student_id)

    if parents:
        # Sort so primary is always first
        parents.sort(key=lambda x: not x.is_primary)
        for g_link in parents:
            g = g_link.guardian
            badge = "🏆 Primary" if g_link.is_primary else "Secondary"
            st.markdown(
                f"**{g.full_name}** ({g_link.relationship}) — {badge}  \n📞 {g.phone_primary} | {g.phone_secondary or ''}"
            )
    else:
        st.warning("No parent linked.")

    st.divider()

    # 2. Enrollments & Attendance Summary
    st.markdown("#### Enrollments & Academic History")

    enrollments = get_student_enrollments(student_id)

    if enrollments:
        # Build enriched view for enrollments
        enr_data = []
        has_debt = False
        for e in enrollments:
            g = get_group_by_id(e.group_id)
            group_name = g.name if g else f"Group #{e.group_id}"

            # Fetch attendance summary for this enrollment
            att_summary = get_attendance_summary(e.id)
            att_str = f"✅ {att_summary.sessions_attended}   ❌ {att_summary.sessions_missed}"

            balance_data = fin_srv.get_enrollment_balance(e.id)
            balance = balance_data["balance"] if balance_data else None
            if e.status == "active" and balance is not None and balance < 0:
                has_debt = True

            enr_data.append(
                {
                    "Group": group_name,
                    "Level": f"L{e.level_number}",
                    "Status": str(e.status).capitalize(),
                    "Amount Due": f"{e.amount_due} EGP" if e.amount_due else "-",
                    "Discount": f"-{e.discount_applied} EGP"
                    if e.discount_applied
                    else "-",
                    "Acct balance": f"{balance:.0f} EGP" if balance is not None else "—",
                    "Attendance": att_str,
                    "Enrolled On": str(e.enrolled_at) if e.enrolled_at else "",
                }
            )

        st.caption("Account balance: negative = debt owed, positive = credit (P6).")
        st.dataframe(pd.DataFrame(enr_data), hide_index=True, use_container_width=True)

        if has_debt:
            if st.button("💰 Go to Finance — Create Receipt", use_container_width=True):
                st.switch_page("pages/0_Dashboard.py")
    else:
        st.info("Student has no enrollment history.")

    # 3. Quick Action: Enroll
    with st.expander("➕ Enroll in Group"):
        st.markdown(
            "Use the dedicated Enrollment Management page to enroll this student, manage transfers, or apply discounts."
        )
        if st.button("Go to Enrollment Page", type="primary"):
            st.switch_page("pages/5_Enrollment.py")

    st.divider()

    # 4. Competition History
    st.markdown("#### 🏆 Competitions & Teams")

    comp_history = comp_srv.get_student_competitions(student_id)
    if comp_history:
        comp_df_data = []
        for h in comp_history:
            team = h["team"]
            comp = h["competition"]
            cat = h["category"]
            membership = h["membership"]

            comp_df_data.append(
                {
                    "Competition": comp.name if comp else "Unknown",
                    "Edition": comp.edition if comp and comp.edition else "—",
                    "Category": cat.category_name if cat else "—",
                    "Team": team.team_name,
                    "Role/Fee": "✅ Paid" if membership.fee_paid else "❌ Unpaid Fee",
                }
            )

        st.dataframe(
            pd.DataFrame(comp_df_data), hide_index=True, use_container_width=True
        )
    else:
        st.info("Student is not registered in any competitions.")

    st.divider()

    if st.button("⬅️ Back to Search", use_container_width=True):
        del st.session_state["nav_target_student_id"]
        st.rerun()
