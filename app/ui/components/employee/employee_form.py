import streamlit as st

from app.modules.auth.auth_models import UserCreate
from app.modules.auth.role_types import UserRole
from app.modules.hr import hr_service
from app.modules.hr.hr_models import EmployeeCreate
from app.shared.constants import EMPLOYMENT_TYPES, EmploymentType

_ROLE_OPTIONS = list(UserRole)

_EMPLOYMENT_LABELS: dict[EmploymentType, str] = {
    "full_time": "Full-time",
    "part_time": "Part-time",
    "contract": "Contract",
}


def render_edit_employee_form(emp):
    with st.form(f"edit_emp_{emp.id}"):
        e_name = st.text_input("Full Name *", value=emp.full_name)
        e_phone = st.text_input("Phone", value=emp.phone or "")
        e_title = st.text_input("Job Title", value=emp.job_title or "")
        e_active = st.checkbox("Active Status", value=emp.is_active)

        if st.form_submit_button("Save Details", type="primary"):
            try:
                hr_service.update_employee_only(
                    emp.id,
                    EmployeeCreate(
                        full_name=e_name.strip(),
                        phone=e_phone.strip() or None,
                        job_title=e_title.strip() or None,
                        is_active=e_active,
                    ),
                )
                st.success("Updated successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")


def render_add_employee_form():
    with st.form("add_emp_new"):
        c1, c2 = st.columns(2)
        with c1:
            n_name = st.text_input("Full Name *")
            n_phone = st.text_input("Phone")
        with c2:
            n_title = st.text_input("Job Title (e.g. Instructor, Robot Builder)")
            n_emp_type = st.selectbox(
                "Employment type *",
                EMPLOYMENT_TYPES,
                index=1,
                format_func=lambda x: _EMPLOYMENT_LABELS[x],
            )
        n_contract_pct = None
        if n_emp_type == "contract":
            n_contract_pct = st.number_input(
                "Contract percentage (%)",
                min_value=0.0,
                max_value=100.0,
                value=25.0,
                step=0.5,
            )

        create_login = st.checkbox("Create System Login Account?")

        if create_login:
            st.markdown("---")
            l_user = st.text_input("Username *")
            l_role = st.selectbox(
                "Role *",
                _ROLE_OPTIONS,
                format_func=lambda r: r.value,
            )
            l_pass = st.text_input("Temporary Password *", type="password")

        if st.form_submit_button("Adding Employee Data", type="primary"):
            if not n_name:
                st.error("Name is required.")
                return
            try:
                if create_login:
                    emp_in = EmployeeCreate(
                        full_name=n_name.strip(),
                        phone=n_phone.strip() or None,
                        job_title=n_title.strip() or None,
                        employment_type=n_emp_type,
                        contract_percentage=n_contract_pct,
                        is_active=True,
                    )
                    user_in = UserCreate(username=l_user.strip(), role=l_role)
                    hr_service.create_staff_account(emp_in, user_in, l_pass)
                    st.success("Employee and Login created.")
                else:
                    hr_service.create_employee_only(
                        EmployeeCreate(
                            full_name=n_name.strip(),
                            phone=n_phone.strip() or None,
                            job_title=n_title.strip() or None,
                            employment_type=n_emp_type,
                            contract_percentage=n_contract_pct,
                            is_active=True,
                        )
                    )
                    st.success("Employee data created.")
                st.rerun()
            except Exception as e:
                st.error(str(e))
