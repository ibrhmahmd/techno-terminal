import streamlit as st
import pandas as pd
from app.db.connection import get_session
from app.modules.crm.crm_models import Guardian
from app.modules.crm.crm_repository import get_guardian_by_id
from app.modules.finance import finance_service as fin_srv
from app.modules.competitions import competition_service as comp_srv
from app.modules.enrollments import get_student_enrollments


def render_parent_detail(parent_id: int):
    with get_session() as db:
        parent = get_guardian_by_id(db, parent_id)

        if not parent:
            st.error("Parent not found.")
            if st.button("⬅️ Back to Search"):
                del st.session_state["nav_target_parent_id"]
                st.rerun()
            return

        # Extract children (students mapped to this guardian)
        children = [link.student for link in parent.student_links]

        # Header section
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("⬅️ Back"):
                del st.session_state["nav_target_parent_id"]
                st.rerun()
        with col2:
            st.subheader(f"Parent Profile: {parent.full_name}")

        st.markdown(
            f"**Relation:** {parent.relation} | **Email:** {parent.email or 'N/A'}"
        )
        st.markdown(
            f"**Primary Phone:** {parent.phone_primary} | **Secondary Form:** {parent.phone_secondary or 'N/A'}"
        )
        if parent.notes:
            st.info(f"**Notes:** {parent.notes}")

        st.divider()

        st.markdown("#### Registered Children")
        if children:
            child_data = []
            for c in children:
                child_data.append(
                    {
                        "Student ID": c.id,
                        "Name": c.full_name,
                        "Age / DOB": str(c.date_of_birth)
                        if c.date_of_birth
                        else "Unknown",
                        "Gender": c.gender.capitalize() if c.gender else "Unknown",
                        "Status": "🟢 Active" if c.is_active else "🔴 Inactive",
                    }
                )

            st.dataframe(
                pd.DataFrame(child_data), hide_index=True, use_container_width=True
            )

            # Financial Overview per child
            st.divider()
            st.markdown("#### 💳 Financial Overview")

            any_balance = False
            for c in children:
                # 1. Course Enrollments
                balances = fin_srv.get_student_financial_summary(c.id)
                active_balances = [b for b in balances if b.get("balance", 0) > 0]

                # 2. Competitions
                comp_history = comp_srv.get_student_competitions(c.id)
                unpaid_comps = [
                    h
                    for h in comp_history
                    if not h["membership"].fee_paid
                    and h["team"].enrollment_fee_per_student
                    and h["team"].enrollment_fee_per_student > 0
                ]

                if active_balances or unpaid_comps:
                    any_balance = True

                    enr_owed = float(sum(b["balance"] for b in active_balances))
                    comp_owed = float(
                        sum(h["team"].enrollment_fee_per_student for h in unpaid_comps)
                    )
                    total_owed = enr_owed + comp_owed

                    st.markdown(f"**{c.full_name}** — 🔴 Owes **{total_owed:.0f} EGP**")

                    for b in active_balances:
                        st.caption(
                            f"  Enrollment #{b['enrollment_id']} | "
                            f"Due: {b['net_due']:.0f} | Paid: {b['total_paid']:.0f} | Balance: {b['balance']:.0f} EGP"
                        )
                    for hc in unpaid_comps:
                        st.caption(
                            f"  Competition: {hc['competition'].name if hc['competition'] else 'Unknown'} "
                            f"({hc['team'].team_name}) | Fee: {hc['team'].enrollment_fee_per_student:.0f} EGP"
                        )
                else:
                    st.markdown(f"**{c.full_name}** — 🟢 No outstanding balance")

            if any_balance:
                if st.button(
                    "💰 Create Receipt for this Parent",
                    type="primary",
                    use_container_width=True,
                ):
                    st.switch_page("pages/7_Finance.py")

    with st.expander("➕ Register a New Child"):
        st.markdown(
            "To register a new child for this parent, head over to Student Management."
        )
        if st.button("Go to Student Management", type="primary"):
            st.switch_page("pages/2_Student_Management.py")

    st.divider()
    if st.button("⬅️ Back to Search", use_container_width=True):
        del st.session_state["nav_target_parent_id"]
        st.rerun()
