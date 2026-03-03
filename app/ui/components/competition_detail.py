import streamlit as st
import pandas as pd
from app.modules.competitions import service as comp_srv
from app.modules.auth.repository import get_employee_by_id
from app.db.connection import get_session


def render_competition_detail(competition_id: int):
    comp_data = comp_srv.get_competition_summary(competition_id)
    if not comp_data:
        st.error("Competition not found.")
        if st.button("⬅️ Back"):
            del st.session_state["selected_competition_id"]
            st.rerun()
        return

    comp = comp_data["competition"]
    categories = comp_data["categories"]

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("⬅️ Back to List", use_container_width=True):
            del st.session_state["selected_competition_id"]
            st.rerun()
    with col2:
        st.subheader(f"🏆 {comp.name}")

    st.markdown(
        f"**Edition:** {comp.edition or '—'} | "
        f"**Date:** {str(comp.competition_date) if comp.competition_date else '—'} | "
        f"**Location:** {comp.location or '—'}"
    )
    if comp.notes:
        st.info(f"**Notes:** {comp.notes}")

    st.divider()

    st.markdown("### Categories & Teams")

    if not categories:
        st.info("No categories defined for this competition yet.")

    with get_session() as db:
        for cat_data in categories:
            cat = cat_data["category"]
            teams = cat_data["teams"]

            st.markdown(f"#### 📂 {cat.category_name}")
            if cat.notes:
                st.caption(cat.notes)

            if not teams:
                st.markdown("*No teams registered in this category.*")
            else:
                for t_data in teams:
                    team = t_data["team"]
                    members = t_data["members"]

                    coach_name = "—"
                    if team.coach_id:
                        coach = get_employee_by_id(db, team.coach_id)
                        if coach:
                            coach_name = coach.full_name

                    fee = (
                        f"{team.enrollment_fee_per_student:.0f} EGP"
                        if team.enrollment_fee_per_student
                        else "Free"
                    )
                    paid_count = sum(1 for m in members if m.fee_paid)

                    with st.expander(
                        f"👥 {team.team_name} — {len(members)} members ({paid_count}/{len(members)} fees paid)"
                    ):
                        st.markdown(
                            f"**Coach:** {coach_name} | **Fee per student:** {fee}"
                        )
                        if members:
                            from app.modules.crm.models import Student

                            member_list = []
                            for m in members:
                                s = db.get(Student, m.student_id)
                                member_list.append(
                                    {
                                        "Student": s.full_name
                                        if s
                                        else f"Student #{m.student_id}",
                                        "Fee Paid": "✅ Yes" if m.fee_paid else "❌ No",
                                        "Payment ID": m.payment_id or "—",
                                    }
                                )
                            st.dataframe(
                                pd.DataFrame(member_list),
                                hide_index=True,
                                use_container_width=True,
                            )
                        else:
                            st.caption("No members in this team.")
            st.write("")  # Spacing between categories

    st.divider()

    with st.expander("➕ Add New Category"):
        new_cat_name = st.text_input("Category Name", key=f"d_cat_{competition_id}")
        new_cat_notes = st.text_input(
            "Notes (optional)", key=f"d_notes_{competition_id}"
        )
        if st.button("Save Category", type="primary", key=f"d_save_{competition_id}"):
            try:
                comp_srv.add_category(
                    competition_id, new_cat_name, new_cat_notes or None
                )
                st.success("Category added!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ {e}")
