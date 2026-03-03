import streamlit as st
from app.ui.components.auth_guard import require_auth
from app.ui.components.parent_overview import render_parent_overview
from app.ui.components.parent_detail import render_parent_detail

st.set_page_config(page_title="Parent Management", layout="wide")
require_auth()

st.title("👥 Parent Management")
st.markdown(
    "Search existing parents, create profiles, and review their registered children."
)

# Router logic: Either show the Overview or the Detail view
if "nav_target_parent_id" in st.session_state:
    render_parent_detail(st.session_state["nav_target_parent_id"])
else:
    render_parent_overview()
