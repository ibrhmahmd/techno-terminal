from app.db.connection import get_session
from app.modules.auth.auth_models import Employee
from app.shared.exceptions import NotFoundError
from . import hr_repository as repo
from .hr_schemas import CreateEmployeeDTO, UpdateEmployeeDTO

def list_all_employees() -> list[Employee]:
    with get_session() as session:
        return list(repo.get_all_employees(session))

def get_employee_by_id(emp_id: int) -> Employee:
    with get_session() as session:
        emp = repo.get_employee_by_id(session, emp_id)
        if not emp: raise NotFoundError(f"Employee {emp_id} not found")
        return emp

def create_employee(dto: CreateEmployeeDTO) -> Employee:
    with get_session() as session:
        emp = repo.create_employee(session, dto.model_dump(exclude_unset=True))
        session.commit()
        session.refresh(emp)
        return emp

def update_employee(emp_id: int, dto: UpdateEmployeeDTO) -> Employee:
    with get_session() as session:
        emp = repo.update_employee(session, emp_id, dto.model_dump(exclude_unset=True))
        if not emp: raise NotFoundError(f"Employee {emp_id} not found")
        session.commit()
        session.refresh(emp)
        return emp
