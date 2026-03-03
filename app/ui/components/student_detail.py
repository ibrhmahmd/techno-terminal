import streamlit as st
import pandas as pd
from app.modules.crm.repository import get_student_by_id, get_student_guardians
from app.modules.enrollments.service import get_student_enrollments
from app.modules.attendance.service import get_attendance_summary
from app.modules.academics.service import get_group_by_id
from app.db.connection import get_session


def render_student_detail(student_id: int):
    with get_session() as db:
        student = get_student_by_id(db, student_id)

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
        st.info(f"**Medical/Notes:** {student.notes}")

    st.divider()

    # 1. Parent Info
    with get_session() as db:
        guardians = get_student_guardians(db, student_id)

    st.markdown("#### Parent/Guardian Details")
    if guardians:
        # Sort so primary is always first
        guardians.sort(key=lambda x: not x.is_primary)
        for g_link in guardians:
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
        for e in enrollments:
            g = get_group_by_id(e.group_id)
            group_name = g.name if g else f"Group #{e.group_id}"

            # Fetch attendance summary for this enrollment
            att_summary = get_attendance_summary(e.id)
            att_str = f"✅ {att_summary.get('sessions_attended', 0)}   ❌ {att_summary.get('sessions_missed', 0)}"

            enr_data.append(
                {
                    "Group": group_name,
                    "Level": f"L{e.level_number}",
                    "Status": str(e.status).capitalize(),
                    "Amount Due": f"{e.amount_due} EGP" if e.amount_due else "-",
                    "Discount": f"-{e.discount_applied} EGP"
                    if e.discount_applied
                    else "-",
                    "Attendance": att_str,
                    "Enrolled On": str(e.enrolled_at.date()) if e.enrolled_at else "",
                }
            )

        st.dataframe(pd.DataFrame(enr_data), hide_index=True, use_container_width=True)
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

    if st.button("⬅️ Back to Search", use_container_width=True):
        del st.session_state["nav_target_student_id"]
        st.rerun()
