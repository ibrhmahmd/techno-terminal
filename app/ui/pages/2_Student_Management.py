import streamlit as st
import pandas as pd
from datetime import datetime
from app.ui.components.auth_guard import require_auth
from app.modules.crm import service as crm_srv

# Enforce auth
require_auth()

st.title("🎓 Student Management")
st.markdown("Register new students and link them to their guardians.")

# --- Top tabs ---
tab_register, tab_search = st.tabs(["Register Student", "Search Students"])

# --- TAB 1: Register Student ---
with tab_register:
    st.subheader("Link to Guardian")

    # 1. First find the guardian
    guardian_search = st.text_input(
        "Search Guardian by Name or Phone (min 2 chars)", key="gs"
    )
    selected_guardian_id = None

    if guardian_search and len(guardian_search) >= 2:
        guardians = crm_srv.search_guardians(guardian_search)
        if guardians:
            guardian_options = {
                f"{g.full_name} ({g.phone_primary})": g.id for g in guardians
            }
            selected_gui = st.selectbox(
                "Select Primary Guardian", options=list(guardian_options.keys())
            )
            selected_guardian_id = guardian_options[selected_gui]
        else:
            st.warning(
                "No guardians found. Please register the guardian first in Guardian Management."
            )

    st.divider()

    # 2. Student Form (only enabled if guardian selected)
    st.subheader("Student Details")

    if selected_guardian_id:
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
                    data = {
                        "full_name": full_name.strip(),
                        "date_of_birth": birth_date,
                        "gender": gender,
                        "phone": phone.strip() if phone else None,
                        "notes": notes.strip() if notes else None,
                    }
                    try:
                        new_student, siblings = crm_srv.register_student(
                            data, guardian_id=selected_guardian_id, relationship="Child"
                        )
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

                    except ValueError as e:
                        st.error(f"❌ {str(e)}")
                    except Exception as e:
                        st.error(f"❌ An unexpected error occurred: {str(e)}")
    else:
        st.info(
            "Please search and select a Guardian above to enable the student registration form."
        )

# --- TAB 2: Search Students ---
with tab_search:
    st.subheader("Search Students")
    student_search = st.text_input("Search Student by Name (min 2 chars)", key="ss")

    if student_search and len(student_search) >= 2:
        students = crm_srv.search_students(student_search)
        if students:
            df = pd.DataFrame([s.model_dump() for s in students])
            display_cols = [
                "id",
                "full_name",
                "date_of_birth",
                "gender",
                "phone",
                "is_active",
            ]
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No students found matching your search.")
