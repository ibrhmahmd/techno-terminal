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

        with st.expander("✏️ Edit Family Information"):
            with st.form(f"edit_parent_{parent.id}"):
                c1, c2 = st.columns(2)
                with c1:
                    e_name = st.text_input("Full Name *", value=parent.full_name)
                    e_phone = st.text_input("Primary Phone *", value=parent.phone_primary)
                    rel_opts = ["Father", "Mother", "Guardian", "Other"]
                    e_rel = st.selectbox("Relationship", rel_opts, index=rel_opts.index(parent.relation) if parent.relation in rel_opts else 3)
                with c2:
                    e_phone_sec = st.text_input("Secondary Phone", value=parent.phone_secondary or "")
                    e_email = st.text_input("Email", value=parent.email or "")
                
                e_notes = st.text_area("Notes", value=parent.notes or "")
                
                if st.form_submit_button("Save Changes", type="primary"):
                    from app.modules.crm import crm_service as crm_srv
                    try:
                        crm_srv.update_guardian(parent.id, {
                            "full_name": e_name.strip(),
                            "phone_primary": e_phone.strip(),
                            "phone_secondary": e_phone_sec.strip() or None,
                            "email": e_email.strip() or None,
                            "relation": e_rel,
                            "notes": e_notes.strip() or None
                        })
                        st.success("Family details updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to update: {e}")

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
                    st.switch_page("pages/0_Dashboard.py")

    with st.expander("➕ Register a New Child"):
        st.markdown(
            "To register a new child for this parent, head over to Student Management."
        )
        if st.button("Go to Student Management", type="primary"):
            st.switch_page("pages/1_Directory.py")

    st.divider()
    if st.button("⬅️ Back to Search", use_container_width=True):
        del st.session_state["nav_target_parent_id"]
        st.rerun()
