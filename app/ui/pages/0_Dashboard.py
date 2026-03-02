import streamlit as st
from app.ui.components.auth_guard import require_auth

# Enforce auth
user = require_auth()

st.title("🏠 Dashboard")
st.markdown(f"Welcome back, **{user.username}**!")

st.info(
    "The operational dashboard will be implemented in Phase 6. Use the sidebar to manage Guardians, Students, and Courses."
)
