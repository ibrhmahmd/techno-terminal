import streamlit as st
from app.ui.components.auth_guard import require_auth
from app.ui.components.course_overview import render_course_overview
from app.ui.components.course_detail import render_course_detail

st.set_page_config(page_title="Course Management - Techno Terminal", layout="wide")
require_auth()

st.title("📚 Course Management")
st.markdown("Define and manage courses, update pricing, and view active groups.")

# Router logic: Either show the Overview or the Detail view
if "nav_target_course_id" in st.session_state:
    render_course_detail(st.session_state["nav_target_course_id"])
else:
    render_course_overview()
