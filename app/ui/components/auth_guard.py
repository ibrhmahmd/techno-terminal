import streamlit as st
from app.ui import state


def require_auth():
    if not state.is_authenticated():
        st.switch_page("pages/login.py")
        st.stop()
    return state.get_user()
