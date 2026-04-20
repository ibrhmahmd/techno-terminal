from typing import List, Optional

from sqlalchemy.exc import IntegrityError

from app.db.connection import get_session
from app.core.supabase_clients import get_supabase_admin
from app.modules.hr.hr_models import Employee, EmployeeCreate
from app.modules.auth import UserCreate
from app.modules.auth import is_valid_role
from app.modules.hr import hr_repository as hr_repo
from app.modules.hr.hr_repository import EMPLOYEE_FIELD_KEYS
from app.modules.hr.interfaces.dtos import CreateEmployeeAccountDTO, EmployeeAccountResultDTO
import app.modules.auth.repositories as auth_repo
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


def _assert_no_duplicate_employee_fields(
    session,
    *,
    national_id: str,
    phone: str,
    email: Optional[str],
    exclude_id: Optional[int] = None,
) -> None:
    if hr_repo.find_employee_by_national_id(session, national_id, exclude_id):
        raise ConflictError("Another employee already uses this national ID.")
    if hr_repo.find_employee_by_phone(session, phone, exclude_id):
        raise ConflictError("Another employee already uses this phone number.")
    if email and hr_repo.find_employee_by_email(session, email, exclude_id):
        raise ConflictError("Another employee already uses this email.")


def list_all_employees() -> List[Employee]:
    with get_session() as session:
        employees = hr_repo.get_all_employees(session)
        return list(employees)


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
        _assert_no_duplicate_employee_fields(
            session,
            national_id=payload["national_id"],
            phone=payload["phone"],
            email=payload.get("email"),
            exclude_id=None,
        )
        try:
            emp = hr_repo.create_employee(session, payload)
            session.flush()
            session.refresh(emp)
            return emp
        except IntegrityError as e:
            raise ConflictError(
                "Could not save employee (duplicate phone, email, or national ID)."
            ) from e


def update_employee_only(emp_id: int, emp_in: EmployeeCreate) -> Employee:
    with get_session() as session:
        existing = hr_repo.get_employee_by_id(session, emp_id)
        if not existing:
            raise NotFoundError(f"Employee {emp_id} not found.")
        incoming = emp_in.model_dump()
        merged = existing.model_dump()
        for k in EMPLOYEE_FIELD_KEYS:
            if k not in incoming:
                continue
            if k == "monthly_salary" and incoming[k] is None:
                continue
            merged[k] = incoming[k]
        payload = _normalize_employee_payload(merged, partial=False)
        _assert_no_duplicate_employee_fields(
            session,
            national_id=payload["national_id"],
            phone=payload["phone"],
            email=payload.get("email"),
            exclude_id=emp_id,
        )
        try:
            emp = hr_repo.update_employee(session, emp_id, payload)
            if not emp:
                raise NotFoundError(f"Employee {emp_id} not found.")
            session.flush()
            session.refresh(emp)
            return emp
        except IntegrityError as e:
            raise ConflictError(
                "Could not update employee (duplicate phone, email, or national ID)."
            ) from e


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

        payload = _normalize_employee_payload(emp_in.model_dump(), partial=False)
        _assert_no_duplicate_employee_fields(
            session,
            national_id=payload["national_id"],
            phone=payload["phone"],
            email=payload.get("email"),
            exclude_id=None,
        )

        email_binding = (
            user_in.username if "@" in user_in.username else f"{user_in.username}@system.local"
        )

        try:
            supabase_admin = get_supabase_admin()
            auth_response = supabase_admin.auth.admin.create_user(
                {
                    "email": email_binding,
                    "password": raw_password,
                    "email_confirm": True,
                }
            )
            native_uid = auth_response.user.id
        except Exception as e:
            raise ConflictError(f"Supabase Gateway Error: {str(e)}") from e

        user_data = user_in.model_dump(exclude={"password", "supabase_uid"})
        user_data["supabase_uid"] = native_uid

        try:
            emp, user = hr_repo.create_employee_and_user(session, payload, user_data)
            session.flush()
            session.refresh(emp)
            session.refresh(user)
            return {
                "user_id": user.id,
                "employee_id": emp.id,
                "username": user.username,
                "supabase_uid": native_uid,
            }
        except IntegrityError as e:
            raise ConflictError(
                "Could not save employee (duplicate phone, email, or national ID)."
            ) from e


def list_staff_accounts() -> list[dict]:
    with get_session() as session:
        records = hr_repo.get_all_users_with_employees(session)
        result = []
        for u, e in records:
            result.append(
                {
                    "user_id": u.id,
                    "employee_id": e.id,
                    "username": u.username,
                    "full_name": e.full_name,
                    "role": u.role,
                    "is_active": u.is_active,
                    "phone": e.phone,
                }
            )
        return result


def update_staff_account(user_id: int, is_active: bool, role: str) -> bool:
    if not is_valid_role(role):
        raise ValidationError(f"Invalid role: {role!r}.")
    with get_session() as session:
        hr_repo.update_user_and_employee(session, user_id, is_active, role)
        return True


def create_employee_account(dto: CreateEmployeeAccountDTO) -> EmployeeAccountResultDTO:
    """Create a user account for an existing employee.
    
    Args:
        dto: CreateEmployeeAccountDTO with employee_id, email, password, role
        
    Returns:
        EmployeeAccountResultDTO with created account details
        
    Raises:
        NotFoundError: If employee not found
        ConflictError: If employee already has account or email exists
        ValidationError: If password too short or invalid role
    """
    from datetime import datetime
    from app.modules.hr.interfaces.dtos import CreateEmployeeAccountDTO, EmployeeAccountResultDTO
    from app.modules.auth.models.auth_models import User
    from app.db.connection import get_session
    from app.shared.exceptions import NotFoundError, ConflictError, ValidationError
    from app.core.supabase import get_supabase_admin
    
    MIN_PASSWORD_LENGTH = 8
    VALID_ROLES = {"admin", "system_admin"}
    
    # Validate role
    if dto.role not in VALID_ROLES:
        raise ValidationError(f"Invalid role: {dto.role!r}. Must be 'admin' or 'system_admin'.")
    
    # Validate password length
    if len(dto.password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    
    with get_session() as session:
        # 1. Verify employee exists
        from app.modules.hr.hr_repository import hr_repository
        emp = hr_repository.get_by_id(session, dto.employee_id)
        if not emp:
            raise NotFoundError(f"Employee {dto.employee_id} not found.")
        
        # 2. Check if employee already has an account
        if emp.user_id is not None:
            raise ConflictError(f"Employee {dto.employee_id} already has an account.")
        
        # 3. Check if email is already in use locally
        from app.modules.auth.repositories.auth_repository import auth_repository
        existing_user = auth_repository.get_user_by_email(session, dto.email)
        if existing_user:
            raise ConflictError(f"Email {dto.email} is already registered.")
        
        # 4. Create Supabase user
        try:
            supabase_admin = get_supabase_admin()
            auth_response = supabase_admin.auth.admin.create_user(
                {
                    "email": dto.email,
                    "password": dto.password,
                    "email_confirm": True,
                }
            )
            supabase_uid = auth_response.user.id
        except Exception as e:
            raise ConflictError(f"Supabase account creation failed: {str(e)}") from e
        
        # 5. Create local User record
        user = User(
            username=dto.email,
            email=dto.email,
            role=dto.role,
            supabase_uid=supabase_uid,
            is_active=True,
        )
        session.add(user)
        session.flush()
        session.refresh(user)
        
        # 6. Link employee to user
        emp.user_id = user.id
        session.add(emp)
        session.flush()
        
        return EmployeeAccountResultDTO(
            employee_id=emp.id,
            user_id=user.id,
            email=user.email,
            role=user.role,
            created_at=datetime.utcnow(),
        )
