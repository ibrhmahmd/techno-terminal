import streamlit as st
from app.ui import state
from app.modules.crm import crm_service as crm_srv, RegisterGuardianInput, RegisterStudentInput, RegisterStudentCommandDTO
from app.shared.exceptions import ValidationError, ConflictError

def render_quick_register():
    st.subheader("⚡ Quick Registration")
    st.markdown("Register a new student and parent in one simple step.")
    
    with st.container(border=True):
        with st.form("quick_register_form", clear_on_submit=True):
            col_p, col_s = st.columns(2)
            
            with col_p:
                st.markdown("##### 👩‍👦 Parent Details")
                p_phone = st.text_input("Phone Number (Primary)*", placeholder="01xxxxxxxxx")
                p_name = st.text_input("Full Name*", placeholder="Parent's Name")
                p_relation = st.selectbox("Relationship", ["Father", "Mother", "Guardian", "Other"])
            
            with col_s:
                st.markdown("##### 🎓 Student Details")
                s_name = st.text_input("Student Full Name*", placeholder="Student's Name")
                s_notes = st.text_area("Notes (Optional)", height=68, placeholder="Medical info, allergies, etc.")
                
            with st.expander("➕ Optional Details (Address, School, Medical, etc.)"):
                opt_p, opt_s = st.columns(2)
                with opt_p:
                    p_phone_sec = st.text_input("Parent Secondary Phone", placeholder="01xxxxxxxxx")
                    p_email = st.text_input("Parent Email")
                    p_job = st.text_input("Job Title")
                    p_nid = st.text_input("National ID")
                    p_address = st.text_area("Home Address", height=68)
                    p_notes = st.text_area("Parent Notes (Other)", height=68)
                with opt_s:
                    s_dob = st.date_input("Student Date of Birth", value=None)
                    s_gender = st.selectbox("Student Gender", [None, "male", "female"], format_func=lambda x: "—" if not x else x.capitalize())
                    s_school = st.text_input("School Name")
                    s_grade = st.text_input("Grade Level")
                    s_emerg = st.text_input("Emergency Contact (Name/Phone)")
                    s_med = st.text_area("Medical Notes / Allergies", height=68)
                    s_phone = st.text_input("Student Personal Phone")

            st.markdown("---")
            submit = st.form_submit_button("Create Profiles & Link", type="primary", use_container_width=True)
            
            if submit:
                if not p_phone or not p_name or not s_name:
                    st.error("Please fill all required fields (*)")
                    return
                
                # Format extended metadata into notes columns safely
                p_meta = []
                if p_job: p_meta.append(f"Job: {p_job.strip()}")
                if p_nid: p_meta.append(f"NID: {p_nid.strip()}")
                if p_address: p_meta.append(f"Address: {p_address.strip()}")
                if p_notes: p_meta.append(f"Notes: {p_notes.strip()}")
                final_p_notes = " | ".join(p_meta) if p_meta else None

                s_meta = []
                if s_school: s_meta.append(f"School: {s_school.strip()}")
                if s_grade: s_meta.append(f"Grade: {s_grade.strip()}")
                if s_emerg: s_meta.append(f"Emergency Contact: {s_emerg.strip()}")
                if s_med: s_meta.append(f"Medical: {s_med.strip()}")
                if s_notes: s_meta.append(f"Notes: {s_notes.strip()}")
                final_s_notes = " | ".join(s_meta) if s_meta else None
                
                try:
                    # 1. Find or create guardian
                    guardian, created = crm_srv.find_or_create_guardian(RegisterGuardianInput(
                        full_name=p_name.strip(),
                        phone_primary=p_phone.strip(),
                        phone_secondary=p_phone_sec.strip() if p_phone_sec else None,
                        email=p_email.strip() if p_email else None,
                        relation=p_relation,
                        notes=final_p_notes
                    ))
                    
                    # 2. Register student and link to guardian
                    student_command = RegisterStudentCommandDTO(
                        student_data=RegisterStudentInput(
                            full_name=s_name.strip(),
                            date_of_birth=s_dob if s_dob else None,
                            gender=s_gender,
                            phone=s_phone.strip() if s_phone else None,
                            notes=final_s_notes
                        ),
                        guardian_id=guardian.id,
                        relationship=p_relation,
                        created_by_user_id=state.get_current_user_id(),
                    )
                    student, siblings = crm_srv.register_student(student_command)
                    
                    if created:
                        st.success(f"✅ Created new Parent: **{guardian.full_name}** and Student: **{student.full_name}**")
                    else:
                        st.success(f"✅ Added Student: **{student.full_name}** to existing Parent: **{guardian.full_name}**")
                    
                    if siblings:
                        st.info(f"💡 Note: This student has {len(siblings)} sibling(s) registered under this parent.")
                        
                except ValidationError as e:
                    st.error(f"❌ Invalid Input: {e.message}")
                except ConflictError as e:
                    st.error(f"❌ Conflict: {e.message}")
                except Exception as e:
                    st.error(f"❌ Unexpected Error: {e}")
