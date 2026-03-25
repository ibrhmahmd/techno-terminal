import streamlit as st
import pandas as pd
from datetime import date

from app.modules.competitions import competition_service as comp_srv
from app.modules.hr import hr_service as hr_srv
from app.modules.crm import crm_service as crm_srv
from app.modules.enrollments import enrollment_service as enroll_srv


def render_competition_overview():
    st.title("🏆 Competitions & Teams")

    tab_comps, tab_teams, tab_fees = st.tabs(
        ["🏆 Competitions", "👥 Teams", "💳 Fee Payments"]
    )

    # ── TAB 1: Competitions ───────────────────────────────────────────────────
    with tab_comps:
        col_h, col_btn = st.columns([4, 1])
        col_h.subheader("All Competitions")
        if col_btn.button("➕ New Competition", use_container_width=True):
            st.session_state["show_new_comp"] = True

        # Create new competition form
        if st.session_state.get("show_new_comp"):
            with st.expander("New Competition", expanded=True):
                nc1, nc2 = st.columns(2)
                c_name = nc1.text_input("Name *", key="nc_name")
                c_edition = nc2.text_input("Edition (e.g. 2026)", key="nc_edition")
                nc3, nc4 = st.columns(2)
                c_date = nc3.date_input(
                    "Competition Date", key="nc_date", value=date.today()
                )
                c_location = nc4.text_input("Location", key="nc_location")
                c_notes = st.text_area("Notes", key="nc_notes", height=70)
                col_save, col_cancel = st.columns(2)
                if col_save.button("✅ Save Competition", type="primary"):
                    try:
                        comp_srv.create_competition(
                            c_name, c_edition, c_date, c_location, c_notes
                        )
                        st.success(f"Competition '{c_name}' created!")
                        st.session_state["show_new_comp"] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")
                if col_cancel.button("Cancel"):
                    st.session_state["show_new_comp"] = False
                    st.rerun()

        # List competitions
        competitions = comp_srv.list_competitions()
        if competitions:
            comp_data = [
                {
                    "ID": c.id,
                    "Name": c.name,
                    "Edition": c.edition or "—",
                    "Date": str(c.competition_date) if c.competition_date else "—",
                    "Location": c.location or "—",
                }
                for c in competitions
            ]
            df = pd.DataFrame(comp_data)
            event = st.dataframe(
                df.drop(columns=["ID"]),
                hide_index=True,
                use_container_width=True,
                selection_mode="single-row",
                on_select="rerun",
            )
            if event.selection.rows:
                idx = event.selection.rows[0]
                st.session_state["selected_competition_id"] = competitions[idx].id
                st.rerun()
        else:
            st.info("No competitions yet. Create one above.")

    # ── TAB 2: Teams ──────────────────────────────────────────────────────────
    with tab_teams:
        st.subheader("Manage Teams")
        competitions = comp_srv.list_competitions()
        if not competitions:
            st.info("No competitions yet. Create one in the Competitions tab.")
        else:
            sel_comp = st.selectbox(
                "Select Competition", 
                options=competitions, 
                format_func=lambda c: f"{c.name} ({c.edition or c.id})",
                key="team_comp"
            )
            categories = comp_srv.list_categories(sel_comp.id)

            c_left, c_right = st.columns([2, 1])
            with c_right:
                if st.button("➕ Add Category", use_container_width=True):
                    st.session_state["show_new_cat"] = True

            if st.session_state.get("show_new_cat"):
                with st.expander("New Category", expanded=True):
                    cat_name = st.text_input("Category Name *", key="cat_name")
                    cat_notes = st.text_input("Notes", key="cat_notes")
                    cc1, cc2 = st.columns(2)
                    if cc1.button("Save Category", type="primary"):
                        try:
                            comp_srv.add_category(
                                sel_comp.id, cat_name, cat_notes or None
                            )
                            st.success("Category added!")
                            st.session_state["show_new_cat"] = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ {e}")
                    if cc2.button("Cancel Category"):
                        st.session_state["show_new_cat"] = False
                        st.rerun()

            if not categories:
                st.info("No categories yet for this competition.")
            else:
                sel_cat = st.selectbox(
                    "Select Category",
                    categories,
                    format_func=lambda c: c.category_name,
                    key="team_cat",
                )
                teams = comp_srv.list_teams(sel_cat.id)

                if teams:
                    for team in teams:
                        members = comp_srv.list_team_members(team.id)
                        paid = sum(1 for m in members if m["fee_paid"])
                        with st.expander(
                            f"👥 {team.team_name} — {len(members)} members ({paid}/{len(members)} fees paid)"
                        ):
                            if members:
                                st.dataframe(
                                    pd.DataFrame(members)[
                                        ["student_name", "fee_paid", "payment_id"]
                                    ].rename(
                                        columns={
                                            "student_name": "Student",
                                            "fee_paid": "Fee Paid",
                                            "payment_id": "Payment ID",
                                        }
                                    ),
                                    hide_index=True,
                                    use_container_width=True,
                                )
                            else:
                                st.caption("No members.")
                else:
                    st.info("No teams for this category yet.")

                st.divider()
                with st.expander("➕ Register a New Team in this Category"):
                    t_name = st.text_input("Team Name *", key="t_name")
                    t_fee = st.number_input(
                        "Fee per Student (EGP)", min_value=0.0, step=50.0, key="t_fee"
                    )

                    # Coach selection
                    instructors = hr_srv.get_active_instructors()
                    t_coach = st.selectbox(
                        "Coach (optional)", 
                        options=[None] + instructors, 
                        format_func=lambda i: "— None —" if i is None else i.full_name,
                        key="t_coach"
                    )
                    t_coach_id = t_coach.id if t_coach else None

                    # Link to a group roster (optional, for student selection)
                    import app.modules.academics as acad_srv

                    all_groups = acad_srv.get_all_active_groups_enriched()
                    t_group = st.selectbox(
                        "Source Group (optional)",
                        options=[None] + all_groups,
                        format_func=lambda g: "— Select group to pick students —" if g is None else f"{g.group_name} ({g.course_name})",
                        key="t_group",
                    )
                    t_group_id = t_group.id if t_group else None

                    selected_student_ids = []
                    if t_group_id:
                        roster = enroll_srv.get_group_roster(t_group_id, None)
                        if roster:
                            from app.modules.crm.crm_models import Student
                            from app.db.connection import get_session

                            student_opts = {}
                            with get_session() as db:
                                for enr in roster:
                                    s = db.get(Student, enr.student_id)
                                    if s:
                                        student_opts[s.full_name] = s.id
                            sel_names = st.multiselect(
                                "Select Students",
                                list(student_opts.keys()),
                                key="t_students",
                            )
                            selected_student_ids = [student_opts[n] for n in sel_names]

                    if st.button("✅ Register Team", type="primary"):
                        try:
                            result = comp_srv.register_team(
                                category_id=sel_cat.id,
                                team_name=t_name,
                                student_ids=selected_student_ids,
                                coach_id=t_coach_id,
                                group_id=t_group_id,
                                fee_per_student=t_fee or None,
                            )
                            st.success(
                                f"✅ Team '{result['team'].team_name}' registered with {result['members_added']} members!"
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ {e}")

    # ── TAB 3: Fee Payments ───────────────────────────────────────────────────
    with tab_fees:
        st.subheader("Competition Fee Payments")
        competitions = comp_srv.list_competitions()
        if not competitions:
            st.info("No competitions yet.")
        else:
            sel_comp2 = st.selectbox(
                "Select Competition", 
                options=competitions, 
                format_func=lambda c: f"{c.name} ({c.edition or c.id})",
                key="fee_comp"
            )
            categories2 = comp_srv.list_categories(sel_comp2.id)

            if not categories2:
                st.info("No categories for this competition.")
            else:
                sel_cat2 = st.selectbox(
                    "Select Category",
                    categories2,
                    format_func=lambda c: c.category_name,
                    key="fee_cat",
                )
                teams2 = comp_srv.list_teams(sel_cat2.id)

                if not teams2:
                    st.info("No teams in this category.")
                else:
                    sel_team2 = st.selectbox(
                        "Select Team",
                        teams2,
                        format_func=lambda t: t.team_name,
                        key="fee_team",
                    )
                    members2 = comp_srv.list_team_members(sel_team2.id)

                    if not members2:
                        st.info("No members in this team.")
                    else:
                        fee = sel_team2.enrollment_fee_per_student or 0.0
                        st.markdown(f"**Fee per student:** {fee:.0f} EGP")

                        for m in members2:
                            col_name, col_status, col_btn = st.columns([3, 2, 2])
                            col_name.markdown(f"👤 {m['student_name']}")
                            if m["fee_paid"]:
                                col_status.success("✅ Paid")
                            else:
                                col_status.warning("❌ Unpaid")
                                # Parent search for this student
                                gkeys = [
                                    k
                                    for k in st.session_state
                                    if k == f"fee_g_{m['student_id']}"
                                ]

                                # Auto-mark as paid if fee is 0
                                if fee <= 0:
                                    if col_btn.button(
                                        "💳 Grant Access (Free)",
                                        key=f"pay_{m['student_id']}",
                                        help="Mark as paid since fee is 0",
                                    ):
                                        try:
                                            # We just mark fee_paid without a real receipt for free teams
                                            from app.db.connection import get_session

                                            with get_session() as db:
                                                from app.modules.competitions.competition_repository import (
                                                    mark_fee_paid,
                                                )

                                                mark_fee_paid(
                                                    db,
                                                    sel_team2.id,
                                                    m["student_id"],
                                                    None,
                                                )
                                            st.success("✅ Granted!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ {e}")
                                else:
                                    if col_btn.button(
                                        f"💳 Pay", key=f"pay_{m['student_id']}"
                                    ):
                                        st.session_state[
                                            f"fee_paying_{m['student_id']}"
                                        ] = True

                                    if st.session_state.get(
                                        f"fee_paying_{m['student_id']}"
                                    ):
                                        with st.container():
                                            g_q = st.text_input(
                                                f"Parent/Parent for {m['student_name']} (name/phone)",
                                                key=f"fee_gq_{m['student_id']}",
                                            )
                                        guardian_id = None
                                        if g_q and len(g_q) >= 2:
                                            gs = crm_srv.search_guardians(g_q)
                                            if gs:
                                                sel_g = st.selectbox(
                                                    "Select Parent",
                                                    options=gs,
                                                    format_func=lambda g: f"{g.full_name} ({g.phone_primary})",
                                                    key=f"fee_gsel_{m['student_id']}",
                                                )
                                                guardian_id = sel_g.id

                                        fc1, fc2 = st.columns(2)
                                        if fc1.button(
                                            "Confirm Payment",
                                            key=f"fee_confirm_{m['student_id']}",
                                            type="primary",
                                        ):
                                            try:
                                                result = comp_srv.pay_competition_fee(
                                                    team_id=sel_team2.id,
                                                    student_id=m["student_id"],
                                                    guardian_id=guardian_id,
                                                    received_by_user_id=None,
                                                )
                                                st.success(
                                                    f"✅ Fee paid! Receipt: {result['receipt_number']} | {result['amount']:.0f} EGP"
                                                )
                                                del st.session_state[
                                                    f"fee_paying_{m['student_id']}"
                                                ]
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"❌ {e}")
                                        if fc2.button(
                                            "Cancel",
                                            key=f"fee_cancel_{m['student_id']}",
                                        ):
                                            del st.session_state[
                                                f"fee_paying_{m['student_id']}"
                                            ]
                                            st.rerun()
