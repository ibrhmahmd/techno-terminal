import streamlit as st
import pandas as pd
from datetime import datetime

from app.ui import state
from app.modules.crm import crm_service as crm_srv, RegisterStudentInput, RegisterStudentCommandDTO
from app.shared.exceptions import NotFoundError, BusinessRuleError, ValidationError


@st.dialog("Register New Student", width="large")
def modal_register_student():
    st.subheader("Link to Parent")

    # 1. First find the parent
    parent_search = st.text_input(
        "Search Parent by Name or Phone (min 2 chars)", key="gs"
    )
    selected_parent_id = None

    if parent_search and len(parent_search) >= 2:
        parents = crm_srv.search_guardians(parent_search)
        if parents:
            parent_options = {
                f"{g.full_name} ({g.phone_primary})": g.id for g in parents
            }
            selected_gui = st.selectbox(
                "Select Primary Parent", options=list(parent_options.keys())
            )
            selected_parent_id = parent_options[selected_gui]
        else:
            st.warning(
                "No parents found. Please register the parent first in Parent Management."
            )

    st.divider()

    # 2. Student Form
    st.subheader("Student Details")

    if selected_parent_id:
        with st.form("new_student_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                full_name = st.text_input("Student Full Name *")
                birth_date = st.date_input(
                    "Date of Birth",
                    min_value=datetime(2000, 1, 1),
                    max_value=datetime.today(),
                )
                gender = st.selectbox("Gender", ["male", "female"])

            with col2:
                phone = st.text_input("Student Phone (Optional)")
                notes = st.text_area("Medical / Staff Notes (Optional)", height=110)

            submit_student = st.form_submit_button("Register Student", type="primary")

            if submit_student:
                if not full_name.strip():
                    st.error("Student Name is required.")
                else:
                    data = RegisterStudentInput(
                        full_name=full_name.strip(),
                        date_of_birth=birth_date,
                        gender=gender,
                        phone=phone.strip() if phone else None,
                        notes=notes.strip() if notes else None,
                    )
                    try:
                        student_command = RegisterStudentCommandDTO(
                            student_data=data,
                            guardian_id=selected_parent_id,
                            relationship="Child",
                            created_by_user_id=state.get_current_user_id(),
                        )
                        new_student, siblings = crm_srv.register_student(student_command)
                        st.success(
                            f"✅ Successfully registered {new_student.full_name} (ID: {new_student.id})!"
                        )

                        if siblings:
                            sibling_names = ", ".join(
                                s["sibling_name"] for s in siblings
                            )
                            st.warning(
                                f"👨‍👩‍👧‍👦 **Sibling(s) detected:** {sibling_names}. "
                                f"Admin may apply a 50 EGP discount per level when enrolling."
                            )

                        st.rerun()

                    except NotFoundError as e:
                        st.warning(f"⚠️ Not found: {e.message}")
                    except ValidationError as e:
                        st.error(f"❌ Invalid input: {e.message}")
                    except BusinessRuleError as e:
                        st.error(f"❌ Not allowed: {e.message}")
                    except Exception as e:
                        st.error(f"❌ An unexpected error occurred: {str(e)}")
    else:
        st.info(
            "Please search and select a Parent above to enable the student registration form."
        )

@st.dialog("Browse All Students", width="large")
def modal_browse_all_students():
    students = crm_srv.list_all_students(limit=1000)
    if not students:
        st.info("No students found.")
        return

    PAGE_SIZE = 15
    if "bs_page" not in st.session_state:
        st.session_state["bs_page"] = 0

    total_pages = (len(students) - 1) // PAGE_SIZE + 1
    start_idx = st.session_state["bs_page"] * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_data = students[start_idx:end_idx]

    df = pd.DataFrame([s.model_dump() for s in page_data])
    display_cols = ["id", "full_name", "date_of_birth", "gender", "phone", "is_active"]
    
    st.markdown("Select a row to view the student profile:")
    event = st.dataframe(
        df[display_cols],
        hide_index=True,
        use_container_width=True,
        selection_mode="single-row",
        on_select="rerun",
    )

    if event.selection.rows:
        sel_idx = event.selection.rows[0]
        st.session_state["nav_target_student_id"] = page_data[sel_idx].id
        st.session_state["bs_page"] = 0
        st.rerun()

    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("⬅️ Prev", disabled=(st.session_state["bs_page"] == 0), key="bs_prev"):
        st.session_state["bs_page"] -= 1
        st.rerun()
    c2.markdown(
        f"<div style='text-align: center'>Page {st.session_state['bs_page'] + 1} of {total_pages}</div>",
        unsafe_allow_html=True,
    )
    if c3.button("Next ➡️", disabled=(st.session_state["bs_page"] >= total_pages - 1), key="bs_next"):
        st.session_state["bs_page"] += 1
        st.rerun()


def render_student_overview():
    col_l, col_btn1, col_btn2 = st.columns([2, 1, 1])
    with col_l:
        st.subheader("Search Students")
    with col_btn1:
        if st.button("📋 Browse All", key="btn_browse_students", use_container_width=True):
            modal_browse_all_students()
    with col_btn2:
        if st.button("➕ Register Student", key="btn_register_student", use_container_width=True):
            modal_register_student()

    student_search = st.text_input(
        "🔍 Search Student by Name (min 2 chars)",
        key="ss",
        help="Type to search and select a student",
    )

    if student_search and len(student_search) >= 2:
        students = crm_srv.search_students(student_search)
        if students:
            st.markdown(
                "Select a student below to view their profile, enrollments, and attendance:"
            )

            df = pd.DataFrame([s.model_dump() for s in students])
            display_cols = [
                "id",
                "full_name",
                "date_of_birth",
                "gender",
                "phone",
                "is_active",
            ]

            event = st.dataframe(
                df[display_cols],
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
            )

            if event.selection.rows:
                sel_idx = event.selection.rows[0]
                st.session_state["nav_target_student_id"] = students[sel_idx].id
                st.rerun()
        else:
            st.info("No students found matching your search.")
    else:
        st.info("Start typing a name to search for a student.")
