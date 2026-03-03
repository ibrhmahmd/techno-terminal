import streamlit as st
from app.ui.components.auth_guard import require_auth
from app.ui.components.student_overview import render_student_overview
from app.ui.components.student_detail import render_student_detail

st.set_page_config(page_title="Student Management", layout="wide")
require_auth()

st.title("🎓 Student Management")
st.markdown("Search existing students, create profiles, and review academic history.")

# Router logic: Either show the Overview or the Detail view
if "nav_target_student_id" in st.session_state:
    render_student_detail(st.session_state["nav_target_student_id"])
else:
    render_student_overview()
