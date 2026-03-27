import streamlit as st
import pandas as pd
from app.modules.competitions import competition_service as comp_srv
from app.modules.hr.hr_service import get_employee_by_id
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

    with st.expander("✏️ Edit / Delete Competition"):
        e1, e2 = st.columns(2)
        u_name = e1.text_input("Name", value=comp.name, key="uc_name")
        u_edition = e2.text_input("Edition", value=comp.edition or "", key="uc_edition")
        e3, e4 = st.columns(2)
        u_date = e3.date_input(
            "Date", value=comp.competition_date or None, key="uc_date"
        )
        u_location = e4.text_input("Location", value=comp.location or "", key="uc_loc")
        u_notes = st.text_area("Notes", value=comp.notes or "", key="uc_notes")

        c_save, c_del = st.columns(2)
        if c_save.button("✅ Save Changes", type="primary", key="uc_save"):
            comp_srv.update_competition(
                comp.id,
                name=u_name,
                edition=u_edition or None,
                competition_date=u_date,
                location=u_location or None,
                notes=u_notes or None,
            )
            st.success("Updated!")
            st.rerun()
        if c_del.button("🗑️ Delete Competition", key="uc_del"):
            comp_srv.delete_competition(comp.id)
            del st.session_state["selected_competition_id"]
            st.rerun()

    st.divider()

    st.markdown("### Categories & Teams")

    if not categories:
        st.info("No categories defined for this competition yet.")

    with get_session() as db:
        for cat_data in categories:
            cat = cat_data["category"]
            teams = cat_data["teams"]

            cat_col, del_cat_col = st.columns([5, 1])
            with cat_col:
                st.markdown(f"#### 📂 {cat.category_name}")
                if cat.notes:
                    st.caption(cat.notes)
            with del_cat_col:
                if st.button(
                    "🗑️ Delete", key=f"del_cat_{cat.id}", help="Delete Category"
                ):
                    comp_srv.delete_category(cat.id)
                    st.rerun()

            if not teams:
                st.markdown("*No teams registered in this category.*")
            else:
                for t_data in teams:
                    team = t_data["team"]
                    members = t_data["members"]

                    coach_name = "—"
                    if team.coach_id:
                        coach = get_employee_by_id(team.coach_id)
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
                        t_col1, t_col2 = st.columns([3, 1])
                        with t_col1:
                            st.markdown(
                                f"**Coach:** {coach_name} | **Fee per student:** {fee}"
                            )
                        with t_col2:
                            if st.button("🗑️ Delete Team", key=f"del_team_{team.id}"):
                                comp_srv.delete_team(team.id)
                                st.rerun()

                        if members:
                            from app.modules.crm import Student

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
                                        "User ID": m.student_id,
                                    }
                                )
                            st.dataframe(
                                pd.DataFrame(member_list).drop(columns=["User ID"]),
                                hide_index=True,
                                use_container_width=True,
                            )
                        else:
                            st.caption("No members in this team.")

                        # Add member inline form
                        st.markdown("##### ➕ Add Member")
                        am_search = st.text_input(
                            "Search Student by Name", key=f"am_q_{team.id}"
                        )
                        if am_search and len(am_search) >= 2:
                            from app.modules.crm import search_students

                            results = search_students(am_search)
                            if results:
                                existing_ids = [m.student_id for m in members]
                                available = [
                                    s
                                    for s in results
                                    if s.id not in existing_ids and s.is_active
                                ]
                                if available:
                                    sel_s = st.selectbox(
                                        "Select Student",
                                        options=available,
                                        format_func=lambda s: f"{s.full_name} ({s.phone_primary or 'No Phone'})",
                                        key=f"am_sel_{team.id}",
                                    )
                                    if st.button(
                                        "Add to Team",
                                        key=f"am_btn_{team.id}",
                                        type="primary",
                                    ):
                                        try:
                                            comp_srv.add_team_member_to_existing(
                                                team.id, sel_s.id
                                            )
                                            st.success("Member added!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ {e}")
                                else:
                                    st.info(
                                        "All matching active students are already on this team."
                                    )
                            else:
                                st.info("No active students found.")
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
