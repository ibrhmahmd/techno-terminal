import streamlit as st
import pandas as pd
from app.db.connection import get_session
from app.modules.crm.models import Guardian
from app.modules.crm.repository import get_guardian_by_id


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
        else:
            st.warning("No children registered to this parent.")

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
