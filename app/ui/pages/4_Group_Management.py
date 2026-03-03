import streamlit as st
from app.ui.components.auth_guard import require_auth
from app.ui.components.group_overview import render_group_overview
from app.ui.components.group_detail import render_group_detail

st.set_page_config(page_title="Group Management", layout="wide")
require_auth()

st.title("🗂️ Group Management")
st.markdown("Create groups, manage their sessions, and mark student attendance.")

# Router logic: Either show the Overview or the Detail view
if "selected_group_id" in st.session_state:
    render_group_detail(st.session_state["selected_group_id"])
else:
    render_group_overview()
