import streamlit as st

import app.modules.academics as academics_service
from app.modules.auth.auth_service import (
    force_reset_password,
    get_users_for_employee,
    link_employee_to_new_user,
)
from app.modules.auth.role_types import UserRole
from app.modules.hr import hr_service

_ROLE_OPTIONS = list(UserRole)


def render_employee_detail(emp_id: int):
    if st.button("⬅️ Back to Directory"):
        if "nav_target_employee_id" in st.session_state:
            del st.session_state["nav_target_employee_id"]
        st.rerun()

    try:
        emp = hr_service.get_employee_by_id(emp_id)
    except Exception as e:
        st.error(str(e))
        return

    st.header(f"🧑‍🏫 {emp.full_name}")
    nid = getattr(emp, "national_id", None) or "—"
    st.caption(
        f"National ID: {nid} | Job Title: {emp.job_title or 'Unspecified'} | Status: "
        f"{'🟢 Active' if emp.is_active else '🔴 Inactive'}"
    )

    tab_info, tab_proj, tab_sys = st.tabs(
        ["👤 Info & Edit", "📚 Projects & Schedule", "⚙️ System Account"]
    )

    with tab_info:
        from app.ui.components.employee.employee_form import render_edit_employee_form

        render_edit_employee_form(emp)

    with tab_proj:
        st.subheader("Active Groups & Schedules")
        groups = academics_service.get_all_active_groups()
        my_groups = [g for g in groups if g.instructor_id == emp.id]
        if my_groups:
            import pandas as pd

            g_data = [
                {
                    "ID": g.id,
                    "Name": g.name,
                    "Day": g.default_day,
                    "Time": g.default_time_start,
                }
                for g in my_groups
            ]
            st.dataframe(pd.DataFrame(g_data), hide_index=True, use_container_width=True)
        else:
            st.info("No active groups assigned.")

    with tab_sys:
        users = get_users_for_employee(emp.id)
        if users:
            u = users[0]
            st.markdown(f"**Username:** `{u.username}`")
            st.markdown(f"**Role:** `{u.role}`")
            st.markdown(f"**Last Login:** `{u.last_login or 'Never'}`")

            with st.form(f"sys_edit_{u.id}"):
                default_idx = (
                    _ROLE_OPTIONS.index(u.role)
                    if u.role in _ROLE_OPTIONS
                    else 0
                )
                u_role = st.selectbox("Role", _ROLE_OPTIONS, index=default_idx)
                u_active = st.checkbox("Account Active", value=u.is_active)
                if st.form_submit_button("Update Access"):
                    try:
                        hr_service.update_staff_account(u.id, u_active, u_role)
                        st.success("Access updated")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

            with st.expander("Force Password Reset"):
                with st.form(f"pw_reset_{u.id}"):
                    new_pw = st.text_input("New Password", type="password")
                    if st.form_submit_button("Reset Password", type="primary"):
                        try:
                            force_reset_password(u.id, new_pw)
                            st.success("Password reset.")
                        except Exception as e:
                            st.error(str(e))

        else:
            st.warning("No system account linked to this employee.")
            with st.form(f"link_sys_{emp.id}"):
                st.markdown("**Create Linked User Login**")
                n_user = st.text_input("Username *")
                n_role = st.selectbox(
                    "Role *",
                    _ROLE_OPTIONS,
                    format_func=lambda r: r.value,
                )
                n_pass = st.text_input("Temporary Password *", type="password")
                if st.form_submit_button("Create Login", type="primary"):
                    try:
                        link_employee_to_new_user(
                            emp.id, n_user.strip(), n_pass, n_role
                        )
                        st.success("Login linked.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
