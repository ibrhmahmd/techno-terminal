import streamlit as st
from app.core.supabase_clients import get_supabase_anon
from app.modules.auth import get_user_by_supabase_uid, update_last_login

import state

st.set_page_config(page_title="Login — Techno Terminal", layout="centered")

if state.is_authenticated():
    st.switch_page("pages/0_Dashboard.py")

st.title("Techno future")
st.subheader("Admin Login")

with st.form("login_form"):
    username = st.text_input("Username / Email")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login", use_container_width=True)

if submitted:
    supabase = get_supabase_anon()
    
    # Handle legacy usernames by wrapping them in the dummy domain established in hr_service
    email_binding = username if "@" in username else f"{username}@system.local"
    
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email_binding, 
            "password": password
        })
        
        if response.user:
            # Login successful against Supabase. Fetch our local Postgres profile!
            local_user = get_user_by_supabase_uid(response.user.id)
            if local_user and local_user.is_active:
                state.set_user(local_user)
                update_last_login(local_user.id)
                st.session_state["access_token"] = response.session.access_token
                st.switch_page("pages/0_Dashboard.py")
            else:
                st.error("Login succeeded, but local profile is inactive or unmapped.")
                
    except Exception as e:
        # Supabase intentionally obscures exact error reasons to prevent enumeration attacks
        st.error("Invalid credentials.")
