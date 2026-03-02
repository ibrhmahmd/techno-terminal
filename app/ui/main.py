import streamlit as st
from app.ui import state
from app.ui.components.auth_guard import require_auth

st.set_page_config(page_title="Techno Kids", layout="wide", page_icon="🤖")

user = require_auth()

with st.sidebar:
    st.title("🤖 Techno Kids")
    st.caption(f"**{user.username}** · {user.role}")
    st.divider()

    st.page_link("pages/dashboard.py", label="Dashboard", icon="🏠")

    st.divider()

    if st.button("Logout", use_container_width=True):
        state.clear_session()
        st.switch_page("pages/login.py")
