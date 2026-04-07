import streamlit as st
from app.modules.crm import crm_service as crm_srv, UpdateStudentDTO

def render_edit_student_form(student):
    with st.expander("✏️ Edit Student Information"):
        with st.form(f"edit_student_{student.id}"):
            c1, c2 = st.columns(2)
            with c1:
                es_name = st.text_input("Full Name *", value=student.full_name)
                es_dob = st.date_input("Date of Birth", value=student.date_of_birth)
                es_status = st.checkbox("Account Active", value=student.is_active)
            with c2:
                es_phone = st.text_input("Phone (Personal)", value=student.phone or "")
                es_gender = st.selectbox("Gender", ["male", "female"], index=0 if student.gender == "male" else (1 if student.gender == "female" else 0))
            
            es_notes = st.text_area("Notes", value=student.notes or "")
            
            if st.form_submit_button("Save Changes", type="primary"):
                try:
                    crm_srv.update_student(student.id, UpdateStudentDTO(
                        full_name=es_name.strip(),
                        phone=es_phone.strip() or None,
                        gender=es_gender,
                        date_of_birth=es_dob,
                        notes=es_notes.strip() or None,
                        is_active=es_status
                    ))
                    st.success("Student details updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update: {e}")
