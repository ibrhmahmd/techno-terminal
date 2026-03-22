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


def _emp_get(emp, attr: str, default=""):
    v = getattr(emp, attr, None)
    if v is None:
        return default
    return v


def _build_employee_create(
    *,
    full_name: str,
    phone: str,
    email: str,
    national_id: str,
    university: str,
    major: str,
    is_graduate: bool,
    job_title: str,
    employment_type: EmploymentType,
    contract_pct: float | None,
    is_active: bool,
) -> EmployeeCreate:
    return EmployeeCreate(
        full_name=full_name.strip(),
        phone=phone.strip(),
        email=email.strip() or None,
        national_id=national_id.strip(),
        university=university.strip(),
        major=major.strip(),
        is_graduate=is_graduate,
        job_title=job_title.strip() or None,
        employment_type=employment_type,
        contract_percentage=contract_pct,
        is_active=is_active,
    )


def render_edit_employee_form(emp):
    lock_key = f"emp_edit_busy_{emp.id}"
    nat = _emp_get(emp, "national_id", "")
    uni = _emp_get(emp, "university", "")
    maj = _emp_get(emp, "major", "")
    ig = bool(getattr(emp, "is_graduate", False))
    et = (emp.employment_type or "part_time") if getattr(emp, "employment_type", None) else "part_time"
    emp_type_idx = (
        EMPLOYMENT_TYPES.index(et) if et in EMPLOYMENT_TYPES else 1
    )

    with st.form(f"edit_emp_{emp.id}"):
        e_name = st.text_input("Full Name *", value=emp.full_name)
        e_phone = st.text_input("Phone *", value=emp.phone or "")
        e_email = st.text_input("Email (optional, unique)", value=emp.email or "")
        e_nid = st.text_input("National ID *", value=nat)
        c1, c2 = st.columns(2)
        with c1:
            e_uni = st.text_input("University *", value=uni)
            e_major = st.text_input("Major *", value=maj)
        with c2:
            e_grad = st.checkbox("Graduate", value=ig)
        e_title = st.text_input("Job Title", value=emp.job_title or "")
        e_emp_type = st.selectbox(
            "Employment type *",
            EMPLOYMENT_TYPES,
            index=emp_type_idx,
            format_func=lambda x: _EMPLOYMENT_LABELS[x],
        )
        e_contract_pct = None
        if e_emp_type == "contract":
            cp = getattr(emp, "contract_percentage", None)
            e_contract_pct = st.number_input(
                "Contract percentage (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(cp if cp is not None else 25.0),
                step=0.5,
            )
        e_active = st.checkbox("Active Status", value=emp.is_active)

        if st.form_submit_button("Save Details", type="primary"):
            if st.session_state.get(lock_key):
                st.warning("Save already in progress.")
                return
            st.session_state[lock_key] = True
            try:
                emp_in = _build_employee_create(
                    full_name=e_name,
                    phone=e_phone,
                    email=e_email,
                    national_id=e_nid,
                    university=e_uni,
                    major=e_major,
                    is_graduate=e_grad,
                    job_title=e_title,
                    employment_type=e_emp_type,
                    contract_pct=e_contract_pct,
                    is_active=e_active,
                )
                hr_service.update_employee_only(emp.id, emp_in)
                st.success("Updated successfully.")
                st.session_state.pop(lock_key, None)
                st.rerun()
            except Exception as e:
                st.session_state.pop(lock_key, None)
                st.error(f"Error: {e}")


def render_add_employee_form():
    lock_key = "emp_add_busy"
    with st.form("add_emp_new"):
        c1, c2 = st.columns(2)
        with c1:
            n_name = st.text_input("Full Name *")
            n_phone = st.text_input("Phone *")
            n_nid = st.text_input("National ID * (min 10 characters)")
        with c2:
            n_email = st.text_input("Email (optional, unique)")
            n_uni = st.text_input("University *")
            n_major = st.text_input("Major *")
        n_grad = st.checkbox("Graduate", value=False)
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
            if st.session_state.get(lock_key):
                st.warning("Submission already in progress.")
                return
            if not n_name or not n_phone or not n_nid or not n_uni or not n_major:
                st.error("Please fill all required fields (name, phone, national ID, university, major).")
                return
            st.session_state[lock_key] = True
            try:
                emp_in = _build_employee_create(
                    full_name=n_name,
                    phone=n_phone,
                    email=n_email,
                    national_id=n_nid,
                    university=n_uni,
                    major=n_major,
                    is_graduate=n_grad,
                    job_title=n_title,
                    employment_type=n_emp_type,
                    contract_pct=n_contract_pct,
                    is_active=True,
                )
                if create_login:
                    if not l_user or not l_pass:
                        st.error("Username and password are required for login.")
                        st.session_state.pop(lock_key, None)
                        return
                    user_in = UserCreate(username=l_user.strip(), role=l_role)
                    hr_service.create_staff_account(emp_in, user_in, l_pass)
                    st.success("Employee and login created.")
                else:
                    hr_service.create_employee_only(emp_in)
                    st.success("Employee data created.")
                st.session_state.pop(lock_key, None)
                st.rerun()
            except Exception as e:
                st.session_state.pop(lock_key, None)
                st.error(str(e))
