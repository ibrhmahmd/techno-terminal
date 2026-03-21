import pandas as pd
import streamlit as st

from app.modules.auth.auth_service import get_users_for_employee
from app.modules.hr import hr_service


def render_employee_directory():
    st.markdown("### 📋 Staff Directory")
    emps = hr_service.list_all_employees()
    if not emps:
        st.info("No employees found.")
        return

    data = []
    for e in emps:
        users = get_users_for_employee(e.id)
        role = users[0].role if users else "None"
        username = users[0].username if users else "None"
        data.append(
            {
                "id": e.id,
                "Name": e.full_name,
                "Job Title": e.job_title or "-",
                "Phone": e.phone or "-",
                "Sys Role": role,
                "Username": username,
                "Active": "🟢" if e.is_active else "🔴",
            }
        )

    df = pd.DataFrame(data)
    disp_df = df[["Name", "Job Title", "Phone", "Sys Role", "Username", "Active"]]

    st.dataframe(
        disp_df,
        hide_index=True,
        use_container_width=True,
        selection_mode="single-row",
        on_select="rerun",
        key="emp_dir_table",
    )

    if st.session_state["emp_dir_table"]["selection"]["rows"]:
        sel_idx = st.session_state["emp_dir_table"]["selection"]["rows"][0]
        st.session_state["nav_target_employee_id"] = int(df.iloc[sel_idx]["id"])
        st.rerun()
