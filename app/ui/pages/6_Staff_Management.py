import streamlit as st
from app.ui.components.auth_guard import require_auth
from app.ui.components.employee.employee_directory import render_employee_directory
from app.ui.components.employee.employee_detail import render_employee_detail
from app.ui.components.employee.employee_form import render_add_employee_form

st.set_page_config(page_title="Staff Management", layout="wide")
require_auth()

if st.session_state.get("user_role") != "admin":
    st.error("Admin Access Required.")
    st.stop()
    
# Check routing
if "nav_target_employee_id" in st.session_state:
    render_employee_detail(st.session_state["nav_target_employee_id"])
else:
    st.title("👥 Staff Management")
    st.markdown("Manage employee records, HR assignments, and system logins.")
    st.divider()
    
    t_dir, t_add = st.tabs(["📋 Staff Directory", "➕ Add Employee"])
    with t_dir:
        render_employee_directory()
    with t_add:
        render_add_employee_form()
