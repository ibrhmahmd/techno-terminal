import streamlit as st
from app.ui.components.auth_guard import require_auth

user = require_auth()

st.title("Dashboard")
st.caption(f"Welcome back, **{user.username}**")

st.info(
    "Phase 1 complete — authentication is working. More features coming in Phase 2."
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Students", "—", help="Available in Phase 2")

with col2:
    st.metric("Active Groups", "—", help="Available in Phase 2")

with col3:
    st.metric("Unpaid Balances", "—", help="Available in Phase 4")
