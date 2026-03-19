import streamlit as st
import state
from components.auth_guard import require_auth

st.set_page_config(page_title="Techno Kids", layout="wide", page_icon="🤖")

user = require_auth()

with st.sidebar:
    st.title("🤖 Techno Kids")
    st.caption(f"**{user.username}** · {user.role}")
    st.divider()

    st.page_link("pages/0_Dashboard.py", label="Dashboard", icon="🏠")
    st.page_link("pages/1_Directory.py", label="Directory", icon="📇")
    st.page_link("pages/8_Competitions.py", label="Competitions", icon="🏆")
    st.page_link("pages/9_Reports.py", label="Reports", icon="📊")

    st.divider()

    if st.button("Logout", use_container_width=True):
        state.clear_session()
        st.switch_page("pages/login.py")
