from datetime import datetime, timezone
from sqlmodel import Session, select
from app.modules.auth.auth_models import User, Employee


def get_user_by_username(session: Session, username: str) -> User | None:
    stmt = select(User).where(User.username == username)
    return session.exec(stmt).first()


def get_employee_by_id(session: Session, employee_id: int) -> Employee | None:
    return session.get(Employee, employee_id)


def update_password_hash(session: Session, user_id: int, new_hash: str) -> None:
    user = session.get(User, user_id)
    if user:
        user.password_hash = new_hash
        user.updated_at = datetime.now(timezone.utc)
        session.add(user)


def update_last_login(session: Session, user_id: int) -> None:
    user = session.get(User, user_id)
    if user:
        user.last_login = datetime.now(timezone.utc)
        session.add(user)


def get_active_employees(session: Session) -> list[Employee]:
    stmt = select(Employee).where(Employee.is_active == True)
    return session.exec(stmt).all()


# ── Employee Management ───────────────────────────────────────────────────────

def create_employee_and_user(session: Session, emp_data: dict, user_data: dict) -> tuple[Employee, User]:
    emp = Employee(**emp_data)
    session.add(emp)
    session.flush()

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

# ── RepositoryProtocol aliases ────────────────────────────────────────────────
# Primary entity: Employee (User is auth-internal)
get_by_id = get_employee_by_id
list_all = get_active_employees
