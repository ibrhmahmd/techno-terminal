from sqlmodel import Session, select
from app.modules.auth.auth_models import Employee

def get_all_employees(session: Session) -> list[Employee]:
    return session.exec(select(Employee)).all()

def get_employee_by_id(session: Session, emp_id: int) -> Employee | None:
    return session.get(Employee, emp_id)

def create_employee(session: Session, emp_data: dict) -> Employee:
    emp = Employee(**emp_data)
    session.add(emp)
    session.flush()
    return emp

def update_employee(session: Session, emp_id: int, data: dict) -> Employee | None:
    emp = session.get(Employee, emp_id)
    if not emp: return None
    for k, v in data.items():
        if hasattr(emp, k) and k != "id" and v is not None:
            setattr(emp, k, v)
    session.add(emp)
    return emp
