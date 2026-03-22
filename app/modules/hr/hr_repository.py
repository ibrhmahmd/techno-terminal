from sqlmodel import Session, select
from app.shared.datetime_utils import utc_now
from app.modules.auth.auth_models import User
from app.modules.hr.hr_models import Employee

EMPLOYEE_FIELD_KEYS = frozenset(
    {
        "full_name",
        "phone",
        "email",
        "national_id",
        "university",
        "major",
        "is_graduate",
        "job_title",
        "employment_type",
        "monthly_salary",
        "contract_percentage",
        "is_active",
    }
)


def get_employee_by_id(session: Session, employee_id: int) -> Employee | None:
    return session.get(Employee, employee_id)


def find_employee_by_national_id(
    session: Session, national_id: str, exclude_id: int | None = None
) -> Employee | None:
    nid = national_id.strip()
    stmt = select(Employee).where(Employee.national_id == nid)
    if exclude_id is not None:
        stmt = stmt.where(Employee.id != exclude_id)
    return session.exec(stmt).first()


def find_employee_by_phone(
    session: Session, phone: str, exclude_id: int | None = None
) -> Employee | None:
    p = phone.strip()
    stmt = select(Employee).where(Employee.phone == p)
    if exclude_id is not None:
        stmt = stmt.where(Employee.id != exclude_id)
    return session.exec(stmt).first()


def find_employee_by_email(
    session: Session, email: str, exclude_id: int | None = None
) -> Employee | None:
    e = email.strip()
    stmt = select(Employee).where(Employee.email == e)
    if exclude_id is not None:
        stmt = stmt.where(Employee.id != exclude_id)
    return session.exec(stmt).first()


def get_active_employees(session: Session) -> list[Employee]:
    stmt = select(Employee).where(Employee.is_active == True)
    return session.exec(stmt).all()


def get_all_employees(session: Session) -> list[Employee]:
    stmt = select(Employee)
    return session.exec(stmt).all()


def create_employee(session: Session, emp_data: dict) -> Employee:
    clean = {k: v for k, v in emp_data.items() if k in EMPLOYEE_FIELD_KEYS}
    emp = Employee(**clean)
    session.add(emp)
    session.flush()
    return emp


def update_employee(session: Session, employee_id: int, data: dict) -> Employee | None:
    emp = session.get(Employee, employee_id)
    if not emp:
        return None
    for k, v in data.items():
        if k in EMPLOYEE_FIELD_KEYS and k != "id":
            setattr(emp, k, v)
    emp.updated_at = utc_now()
    session.add(emp)
    return emp


def create_employee_and_user(session: Session, emp_data: dict, user_data: dict) -> tuple[Employee, User]:
    emp = create_employee(session, emp_data)
    user_data["employee_id"] = emp.id
    user = User(**user_data)
    session.add(user)
    session.flush()
    return emp, user


def get_all_users_with_employees(session: Session) -> list[tuple[User, Employee]]:
    stmt = select(User, Employee).join(Employee, User.employee_id == Employee.id)
    return session.exec(stmt).all()


def update_user_and_employee(session: Session, user_id: int, is_active: bool, role: str) -> None:
    user = session.get(User, user_id)
    if user:
        user.is_active = is_active
        user.role = role
        if user.employee_id:
            emp = session.get(Employee, user.employee_id)
            if emp:
                emp.is_active = is_active
                session.add(emp)
        session.add(user)


get_by_id = get_employee_by_id
list_all = get_all_employees
