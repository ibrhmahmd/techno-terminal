from typing import List

from app.db.connection import get_session
from app.core.supabase_clients import get_supabase_admin
from app.modules.hr.hr_models import Employee, EmployeeCreate
from app.modules.auth.auth_models import User, UserCreate
from app.modules.auth.role_types import is_valid_role
from app.modules.hr import hr_repository as hr_repo
from app.modules.auth import auth_repository as auth_repo
from app.shared.constants import EMPLOYMENT_TYPES, MIN_PASSWORD_LENGTH
from app.shared.exceptions import ValidationError, ConflictError, NotFoundError

_ALLOWED_EMPLOYMENT = frozenset(EMPLOYMENT_TYPES)


def _normalize_employee_payload(data: dict, *, partial: bool) -> dict:
    """
    Enforce DB-allowed employment_type values and contract_percentage only for contract.
    Mutates data in place; returns data for chaining.
    """
    if partial and "employment_type" not in data:
        return data
    et = data.get("employment_type")
    if et is not None and et not in _ALLOWED_EMPLOYMENT:
        raise ValidationError(
            f"Invalid employment_type {et!r}. "
            f"Allowed: {', '.join(sorted(_ALLOWED_EMPLOYMENT))}."
        )
    if et != "contract":
        data["contract_percentage"] = None
    elif data.get("contract_percentage") is None:
        data["contract_percentage"] = 25.0
    return data

def list_all_employees() -> List[Employee]:
    with get_session() as session:
        employees = hr_repo.get_all_employees(session)
        return list[Employee](employees)
    



def get_employee_by_id(emp_id: int) -> Employee:
    with get_session() as session:
        emp = hr_repo.get_employee_by_id(session, emp_id)
        if not emp:
            raise NotFoundError(f"Employee {emp_id} not found.")
        return emp




def get_active_instructors() -> List[Employee]:
    with get_session() as session:
        return list(hr_repo.get_active_employees(session))


def create_employee_only(emp_in: EmployeeCreate) -> Employee:
    with get_session() as session:
        payload = _normalize_employee_payload(emp_in.model_dump(), partial=False)
        emp = hr_repo.create_employee(session, payload)
        session.commit()
        session.refresh(emp)
        return emp



def update_employee_only(emp_id: int, emp_in: EmployeeCreate) -> Employee:
    with get_session() as session:
        payload = _normalize_employee_payload(
            emp_in.model_dump(exclude_unset=True), partial=True
        )
        emp = hr_repo.update_employee(session, emp_id, payload)
        if not emp:
            raise NotFoundError(f"Employee {emp_id} not found.")
        session.commit()
        session.refresh(emp)
        return emp




def create_staff_account(emp_in: EmployeeCreate, user_in: UserCreate, raw_password: str) -> dict:
    """
    Creates an HR Employee record AND linking Auth User record.
    Delegates cryptography entirely to Supabase Identity Services.
    """
    if len(raw_password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if not is_valid_role(user_in.role):
        raise ValidationError(f"Invalid role: {user_in.role!r}.")

    with get_session() as session:
        existing = auth_repo.get_user_by_username(session, user_in.username)
        if existing:
            raise ConflictError(f"Username {user_in.username} already exists locally.")
            
        # 1. Ask Supabase Admin to natively generate this user Identity
        # Note: Supabase historically requires valid email formats for authentication.
        # We append a dummy domain if username is simply 'admin' etc.
        email_binding = user_in.username if "@" in user_in.username else f"{user_in.username}@system.local"

        try:
            supabase_admin = get_supabase_admin()
            auth_response = supabase_admin.auth.admin.create_user({
                "email": email_binding,
                "password": raw_password,
                "email_confirm": True
            })
            native_uid = auth_response.user.id
        except Exception as e:
            raise ConflictError(f"Supabase Gateway Error: {str(e)}")
            
        # 2. Map the identity back strictly via `supabase_uid`
        emp_data = _normalize_employee_payload(emp_in.model_dump(), partial=False)
        user_data = user_in.model_dump(exclude={"password", "supabase_uid"})
        user_data["supabase_uid"] = native_uid
        
        emp, user = hr_repo.create_employee_and_user(session, emp_data, user_data)
        session.commit()
        return {"user_id": user.id, "employee_id": emp.id, "username": user.username, "supabase_uid": native_uid}

def list_staff_accounts() -> list[dict]:
    with get_session() as session:
        records = hr_repo.get_all_users_with_employees(session)
        result = []
        for u, e in records:
            result.append({
                "user_id": u.id,
                "employee_id": e.id,
                "username": u.username,
                "full_name": e.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "phone": e.phone
            })
        return result

def update_staff_account(user_id: int, is_active: bool, role: str) -> bool:
    if not is_valid_role(role):
        raise ValidationError(f"Invalid role: {role!r}.")
    with get_session() as session:
        hr_repo.update_user_and_employee(session, user_id, is_active, role)
        session.commit()
        return True
