import streamlit as st
from datetime import date, datetime
import app.modules.academics as acad_srv
from app.db.connection import get_session
from app.modules.academics.models import CourseSession
from app.modules.hr.hr_service import get_active_instructors

@st.dialog("✏️ Edit Session Details")
def render_edit_session_form(session_id: int):
    with get_session() as db:
        cs = db.get(CourseSession, session_id)
        
    if not cs:
        st.error("Session not found")
        return
        
    instructors = get_active_instructors()
        
    s_date = st.date_input("Date", value=_coerce_session_date(cs.session_date))
    
    col1, col2 = st.columns(2)
    with col1:
        s_start = st.time_input("Start Time", value=cs.start_time)
        cur_inst = next((i for i, inst in enumerate(instructors) if inst.id == cs.actual_instructor_id), 0) if instructors else 0
        s_inst = st.selectbox("Actual Instructor", options=instructors, format_func=lambda x: x.full_name, index=cur_inst) if instructors else None
    with col2:
        s_end = st.time_input("End Time", value=cs.end_time)
        s_sub = st.checkbox("Is Substitute?", value=cs.is_substitute)
        
    s_notes = st.text_area("Notes", value=cs.notes or "")
    
    if st.button("Save Session Changes", type="primary", use_container_width=True):
        from app.modules.academics.academics_schemas import UpdateSessionDTO
        try:
            acad_srv.update_session(cs.id, UpdateSessionDTO(
                session_date=s_date,
                start_time=s_start,
                end_time=s_end,
                actual_instructor_id=s_inst.id if s_inst else cs.actual_instructor_id,
                is_substitute=s_sub,
                notes=s_notes.strip() or None
            ))
            st.success("Session updated!")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
