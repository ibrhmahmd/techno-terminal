import streamlit as st
from app.modules.auth import service as auth_service
import state

st.set_page_config(page_title="Login — Techno Kids", layout="centered")

if state.is_authenticated():
    st.switch_page("pages/dashboard.py")

st.title("Techno Kids")
st.subheader("Admin Login")

with st.form("login_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login", use_container_width=True)

if submitted:
    user = auth_service.authenticate(username, password)
    if user:
        state.set_user(user)
        st.switch_page("pages/dashboard.py")
    else:
        st.error("Invalid username or password.")
