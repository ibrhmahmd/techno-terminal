import streamlit as st
from app.ui.components.auth_guard import require_auth
from app.ui.components.parent_overview import render_parent_overview
from app.ui.components.parent_detail import render_parent_detail
from app.ui.components.student_overview import render_student_overview
from app.ui.components.student_detail import render_student_detail

st.set_page_config(page_title="Directory - Parents & Students", layout="wide")
require_auth()

st.title("📇 People Directory")
st.markdown("Search existing parents, students, and create profiles.")

# Router logic: If a specific parent or student is selected, show their detail view.
if "nav_target_parent_id" in st.session_state:
    render_parent_detail(st.session_state["nav_target_parent_id"])
elif "nav_target_student_id" in st.session_state:
    render_student_detail(st.session_state["nav_target_student_id"])
else:
    tab_parents, tab_students = st.tabs(["👪 Families (Parents)", "🎓 Students"])
    
    with tab_parents:
        render_parent_overview()
        
    with tab_students:
        render_student_overview()
