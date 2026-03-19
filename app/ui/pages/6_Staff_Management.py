import streamlit as st
import pandas as pd
from app.ui.components.auth_guard import require_auth
from app.modules.auth import auth_service

st.set_page_config(page_title="Staff Management", layout="wide")
require_auth()

if st.session_state["user_role"] != "admin":
    st.error("Admin Access Required.")
    st.stop()

st.title("👥 Staff Management")
st.markdown("Manage employee accounts, assign roles, and perform password resets.")

st.divider()

tab_list, tab_create = st.tabs(["📋 Staff Directory", "➕ Add New Account"])

# ── STAFF DIRECTORY ────────────────────────────────────────────────────────
with tab_list:
    accounts = auth_service.list_staff_accounts()
    if accounts:
        df_acc = pd.DataFrame(accounts)
        
        # Display as a clean dataframe
        disp_df = df_acc.copy()
        disp_df["Status"] = disp_df["is_active"].apply(lambda x: "🟢 Active" if x else "🔴 Inactive")
        disp_df = disp_df.rename(columns={
            "full_name": "Name",
            "username": "Username",
            "role": "Role",
            "phone": "Phone"
        })
        
        st.dataframe(
            disp_df[["Name", "Username", "Role", "Phone", "Status"]], 
            hide_index=True, 
            use_container_width=True,
            selection_mode="single-row",
            on_select="rerun",
            key="staff_table"
        )
        
        if st.session_state["staff_table"]["selection"]["rows"]:
            sel_idx = st.session_state["staff_table"]["selection"]["rows"][0]
            selected_user = df_acc.iloc[sel_idx]
            
            st.divider()
            st.subheader(f"Manage: {selected_user['full_name']}")
            
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                with st.form(f"update_staff_{selected_user['user_id']}"):
                    st.markdown("**Update Status & Role**")
                    u_role = st.selectbox("Role", ["admin", "instructor", "frontend"], 
                                         index=["admin", "instructor", "frontend"].index(selected_user["role"]))
                    u_active = st.checkbox("Account Active", value=selected_user["is_active"])
                    
                    if st.form_submit_button("Savs Changes", type="primary"):
                        try:
                            auth_service.update_staff_account(int(selected_user["user_id"]), u_active, u_role)
                            st.success("Account updated.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                            
            with col_u2:
                with st.form(f"reset_pw_{selected_user['user_id']}"):
                    st.markdown("**Force Password Reset**")
                    new_pw = st.text_input("New Password", type="password")
                    if st.form_submit_button("Reset Password"):
                        try:
                            auth_service.force_reset_password(int(selected_user["user_id"]), new_pw)
                            st.success("Password reset successfully.")
                        except Exception as e:
                            st.error(f"Error: {e}")
                            
    else:
        st.info("No staff accounts found.")

# ── CREATE NEW ACCOUNT ─────────────────────────────────────────────────────
with tab_create:
    st.subheader("Create a New Staff Account")
    with st.form("create_staff_form"):
        c1, c2 = st.columns(2)
        with c1:
            n_name = st.text_input("Full Name *")
            n_user = st.text_input("Username *")
            n_phone = st.text_input("Phone Number")
        with c2:
            n_role = st.selectbox("Role *", ["instructor", "admin", "frontend"])
            n_pass = st.text_input("Temporary Password *", type="password")
            
        st.caption("* Minimum 12 characters for password.")
        
        if st.form_submit_button("Create Account", type="primary"):
            if not n_name or not n_user or not n_pass:
                st.error("Please fill in all required fields.")
            else:
                try:
                    auth_service.create_staff_account(
                        n_user.strip(), n_pass, n_name.strip(), n_role, n_phone.strip() or None
                    )
                    st.success(f"Account for {n_name} created successfully.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
