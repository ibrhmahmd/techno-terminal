import streamlit as st
import pandas as pd
from datetime import date
from app.ui.components.auth_guard import require_auth
from app.modules.crm import service as crm_srv
from app.modules.academics import service as acad_srv
from app.modules.enrollments import service as enroll_srv
from app.shared.exceptions import NotFoundError, BusinessRuleError, ConflictError, ValidationError

require_auth()

st.title("📋 Enrollment Management")
st.markdown("Enroll students in groups, manage transfers, drops, and discounts.")

tab_enroll, tab_manage = st.tabs(["Enroll Student", "Manage Enrollment"])

# ─── TAB 1: Enroll Student ────────────────────────────────────────────────────
with tab_enroll:
    col_s, col_g = st.columns(2)

    with col_s:
        st.subheader("1. Find Student")
        student_q = st.text_input("Search Student (name, min 2 chars)", key="enr_sq")
        selected_student_id = None
        if student_q and len(student_q) >= 2:
            students = crm_srv.search_students(student_q)
            if students:
                opts = {f"{s.full_name} (ID: {s.id})": s.id for s in students}
                sel = st.selectbox("Select Student", list(opts.keys()), key="enr_ss")
                selected_student_id = opts[sel]
            else:
                st.warning("No students found.")

    with col_g:
        st.subheader("2. Select Group")
        groups = acad_srv.get_all_active_groups()
        selected_group_id = None
        if groups:
            group_opts = {f"{g.name} (Level {g.level_number})": g.id for g in groups}
            sel_g = st.selectbox("Select Group", list(group_opts.keys()), key="enr_sg")
            selected_group_id = group_opts[sel_g]

            # Show capacity info
            if selected_group_id:
                sel_group = next(g for g in groups if g.id == selected_group_id)
                roster = enroll_srv.get_group_roster(selected_group_id)
                cap = sel_group.max_capacity or "∞"
                st.caption(f"**Enrolled:** {len(roster)} / {cap}")
        else:
            st.warning("No active groups. Create a group in Course Management first.")

    st.divider()
    st.subheader("3. Enrollment Details")

    if selected_student_id and selected_group_id:
        with st.form("enroll_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                sel_group = next((g for g in groups if g.id == selected_group_id), None)
                # Look up course for default price
                default_price = 0.0

                if sel_group:
                    courses = acad_srv.get_active_courses()
                    course = next(
                        (c for c in courses if c.id == sel_group.course_id), None
                    )
                    if course:
                        default_price = course.price_per_level

                amount_due = st.number_input(
                    "Amount Due (EGP)", min_value=0.0, value=default_price, step=50.0
                )
                apply_discount = st.checkbox("Apply Sibling Discount (−50 EGP)")

            with col_b:
                notes = st.text_area("Notes (Optional)", height=80)

            submit = st.form_submit_button("Enroll Student", type="primary")
            if submit:
                discount = 50.0 if apply_discount else 0.0
                try:
                    enrollment, over_capacity = enroll_srv.enroll_student(
                        student_id=selected_student_id,
                        group_id=selected_group_id,
                        amount_due=amount_due,
                        discount=discount,
                        notes=notes.strip() if notes else None,
                    )
                    st.success(
                        f"✅ Enrolled successfully! Enrollment ID: {enrollment.id}"
                    )
                    if over_capacity:
                        st.warning("⚠️ Group is over capacity. Admin override applied.")
                except NotFoundError as e:
                    st.warning(f"⚠️ Not found: {e.message}")
                except ConflictError as e:
                    st.error(f"❌ Conflict: {e.message}")
                except BusinessRuleError as e:
                    st.error(f"❌ Not allowed: {e.message}")
                except ValidationError as e:
                    st.error(f"❌ Invalid input: {e.message}")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {e}")
    else:
        st.info("Select both a student and a group above to continue.")

# ─── TAB 2: Manage Enrollment ─────────────────────────────────────────────────
with tab_manage:
    st.subheader("Find Enrollment by Student")
    mgmt_q = st.text_input("Search Student (name, min 2 chars)", key="mgmt_q")

    if mgmt_q and len(mgmt_q) >= 2:
        students = crm_srv.search_students(mgmt_q)
        if students:
            mgmt_opts = {f"{s.full_name} (ID: {s.id})": s.id for s in students}
            mgmt_sel = st.selectbox(
                "Select Student", list(mgmt_opts.keys()), key="mgmt_ss"
            )
            mgmt_student_id = mgmt_opts[mgmt_sel]

            enrollments = enroll_srv.get_student_enrollments(mgmt_student_id)
            if enrollments:
                df = pd.DataFrame([e.model_dump() for e in enrollments])
                st.dataframe(
                    df[
                        [
                            "id",
                            "group_id",
                            "level_number",
                            "amount_due",
                            "discount_applied",
                            "status",
                            "enrolled_at",
                        ]
                    ],
                    hide_index=True,
                    use_container_width=True,
                )

                # Action panel
                st.divider()
                active_enrs = [e for e in enrollments if e.status == "active"]
                if active_enrs:
                    enr_opts = {
                        f"Enrollment #{e.id} — Group {e.group_id} L{e.level_number}": e.id
                        for e in active_enrs
                    }
                    sel_enr_label = st.selectbox(
                        "Select Active Enrollment", list(enr_opts.keys())
                    )
                    sel_enr_id = enr_opts[sel_enr_label]

                    ac1, ac2, ac3, ac4 = st.columns(4)
                    with ac1:
                        if st.button(
                            "Apply Discount (−50 EGP)", use_container_width=True
                        ):
                            try:
                                enroll_srv.apply_sibling_discount(sel_enr_id)
                                st.success("Discount applied!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ {e}")
                    with ac2:
                        if st.button("Complete", use_container_width=True):
                            try:
                                enroll_srv.complete_enrollment(sel_enr_id)
                                st.success("Marked as completed.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ {e}")
                    with ac3:
                        if st.button("Drop", use_container_width=True):
                            try:
                                enroll_srv.drop_enrollment(sel_enr_id)
                                st.success("Marked as dropped.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ {e}")
                    with ac4:
                        # Transfer
                        with st.expander("Transfer to Group"):
                            t_groups = acad_srv.get_all_active_groups()
                            t_opts = {
                                f"{g.name} (L{g.level_number})": g.id for g in t_groups
                            }
                            t_sel = st.selectbox(
                                "Target Group", list(t_opts.keys()), key="t_sel"
                            )
                            if st.button("Confirm Transfer", type="primary"):
                                try:
                                    new_enr = enroll_srv.transfer_student(
                                        sel_enr_id, t_opts[t_sel]
                                    )
                                    st.success(
                                        f"Transferred! New enrollment #{new_enr.id}"
                                    )
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ {e}")
            else:
                st.info("This student has no enrollment records.")
        else:
            st.info("No students found.")
