import streamlit as st
import pandas as pd
from app.ui import state
from app.ui.components.auth_guard import require_auth
from app.modules.crm import crm_service as crm_srv
import app.modules.academics as acad_srv
from app.modules.enrollments import enrollment_service as enroll_srv
from app.modules.enrollments.schemas import EnrollStudentInput, TransferStudentInput
from app.shared.exceptions import NotFoundError, BusinessRuleError, ConflictError, ValidationError

st.set_page_config(page_title="Enrollment Wizard - Techno Terminal", layout="wide")
require_auth()

st.title("📋 Enrollment Center")
st.markdown("Enroll students in groups, manage transfers, drops, and discounts.")

tab_enroll, tab_manage = st.tabs(["Enroll Student", "Manage Enrollments"])

# ─── TAB 1: Enroll Student (Progressive Wizard) ────────────────────────────────
with tab_enroll:
    st.subheader("Guided Enrollment Wizard")
    
    # STEP 1: Find Student
    st.markdown("#### 1️⃣ Select Student")
    student_q = st.text_input("Search Student (name, min 2 chars)", key="enr_sq", placeholder="Enter name...")
    selected_student = None
    
    if student_q and len(student_q) >= 2:
        students = crm_srv.search_students(student_q)
        if students:
            selected_student = st.selectbox(
                "Student", 
                options=students, 
                format_func=lambda s: f"{s.full_name} (ID: {s.id})",
                key="enr_ss"
            )
        else:
            st.warning("No students found.")
            
    # STEP 2: Select Group (Only shown if student selected)
    selected_group = None
    if selected_student:
        st.divider()
        st.markdown(f"#### 2️⃣ Select Group for **{selected_student.full_name}**")
        groups = acad_srv.get_all_active_groups()
        
        if groups:
            selected_group = st.selectbox(
                "Available Groups",
                options=groups,
                format_func=lambda g: f"{g.name} (Level {g.level_number})",
                key="enr_sg"
            )
            
            # Show capacity info
            if selected_group:
                roster = enroll_srv.get_group_roster(selected_group.id)
                cap = selected_group.max_capacity or "∞"
                st.caption(f"👥 **Current Enrollment:** {len(roster)} / {cap}")
        else:
            st.warning("No active groups available. Please create one in Course Management first.")
            
    # STEP 3: Enrollment Details & Payment (Only shown if group selected)
    if selected_student and selected_group:
        st.divider()
        st.markdown("#### 3️⃣ Confirm Details")
        
        with st.form("enroll_form", clear_on_submit=False):
            col_a, col_b = st.columns(2)
            
            with col_a:
                # Default price lookup
                default_price = 0.0
                courses = acad_srv.get_active_courses()
                course = next((c for c in courses if c.id == selected_group.course_id), None)
                if course:
                    default_price = course.price_per_level

                amount_due = st.number_input("Amount Due (EGP)", min_value=0.0, value=default_price, step=50.0)
                apply_discount = st.checkbox("Apply Sibling Discount (−50 EGP)")

            with col_b:
                notes = st.text_area("Notes (Optional)", height=68, placeholder="Any special requirements...")

            submit = st.form_submit_button("Confirm & Enroll", type="primary", use_container_width=True)
            
            if submit:
                discount = 50.0 if apply_discount else 0.0
                try:
                    payload = EnrollStudentInput(
                        student_id=selected_student.id,
                        group_id=selected_group.id,
                        amount_due=amount_due,
                        discount=discount,
                        notes=notes.strip() if notes else None,
                        created_by=state.get_current_user_id(),
                    )
                    enrollment, over_capacity = enroll_srv.enroll_student(payload)
                    st.success(f"✅ Enrolled successfully! Enrollment ID: {enrollment.id}")
                    if over_capacity:
                        st.warning("⚠️ Group is over capacity. Admin override applied.")
                        
                except NotFoundError as e: st.warning(f"⚠️ NotFound: {e.message}")
                except ConflictError as e: st.error(f"❌ Conflict: {e.message}")
                except BusinessRuleError as e: st.error(f"❌ Business Rule: {e.message}")
                except ValidationError as e: st.error(f"❌ Validation: {e.message}")
                except Exception as e: st.error(f"❌ Unexpected error: {e}")

# ─── TAB 2: Manage Enrollment ─────────────────────────────────────────────────
with tab_manage:
    st.subheader("Student Enrollment History")
    mgmt_q = st.text_input("Search Student (name, min 2 chars)", key="mgmt_q", placeholder="Enter name...")

    if mgmt_q and len(mgmt_q) >= 2:
        students = crm_srv.search_students(mgmt_q)
        if students:
            mgmt_student = st.selectbox(
                "Select Student to Manage",
                options=students,
                format_func=lambda s: f"{s.full_name} (ID: {s.id})",
                key="mgmt_ss"
            )

            enrollments = enroll_srv.get_student_enrollments(mgmt_student.id)
            if enrollments:
                df = pd.DataFrame([e.model_dump() for e in enrollments])
                st.dataframe(
                    df[["id", "group_id", "level_number", "amount_due", "discount_applied", "status", "enrolled_at"]],
                    hide_index=True,
                    use_container_width=True,
                )

                # Action panel
                st.divider()
                st.markdown("##### ⚙️ Manage Active Enrollments")
                active_enrs = [e for e in enrollments if e.status == "active"]
                if active_enrs:
                    sel_enr = st.selectbox(
                        "Target Enrollment",
                        options=active_enrs,
                        format_func=lambda e: f"ID #{e.id} — Group {e.group_id} L{e.level_number}"
                    )

                    ac1, ac2, ac3, ac4 = st.columns(4)
                    with ac1:
                        if st.button("Apply Discount (−50 EGP)", use_container_width=True):
                            try:
                                enroll_srv.apply_sibling_discount(sel_enr.id)
                                st.success("Discount applied!")
                                st.rerun()
                            except Exception as e: st.error(f"❌ {e}")
                    with ac2:
                        if st.button("Complete", use_container_width=True):
                            try:
                                enroll_srv.complete_enrollment(sel_enr.id)
                                st.success("Marked as completed.")
                                st.rerun()
                            except Exception as e: st.error(f"❌ {e}")
                    with ac3:
                        if st.button("Drop", use_container_width=True):
                            try:
                                enroll_srv.drop_enrollment(sel_enr.id)
                                st.success("Marked as dropped.")
                                st.rerun()
                            except Exception as e: st.error(f"❌ {e}")
                    with ac4:
                        with st.popover("Transfer Group"):
                            t_groups = acad_srv.get_all_active_groups()
                            t_sel = st.selectbox(
                                "Target Group",
                                options=t_groups,
                                format_func=lambda g: f"{g.name} (L{g.level_number})"
                            )
                            if st.button("Confirm Transfer", type="primary"):
                                try:
                                    payload = TransferStudentInput(
                                        from_enrollment_id=sel_enr.id,
                                        to_group_id=t_sel.id,
                                        created_by=state.get_current_user_id(),
                                    )
                                    new_enr = enroll_srv.transfer_student(payload)
                                    st.success(f"Transferred! New ID: #{new_enr.id}")
                                    st.rerun()
                                except Exception as e: st.error(f"❌ {e}")
                else:
                    st.info("No active enrollments available to manage.")
            else:
                st.info("This student has no enrollment records.")
        else:
            st.info("No students found.")
