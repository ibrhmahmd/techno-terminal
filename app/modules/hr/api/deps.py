"""HR HTTP-layer service factories (ADR-0002: api/ → services/)."""

from fastapi import Depends
from sqlmodel import Session
from app.api.dependencies import get_db
from app.core.supabase_clients import get_supabase_admin
from app.modules.hr import EmployeeCrudService, StaffAccountService
from app.modules.hr.repositories import HRUnitOfWork


def get_employee_crud_service(
    session: Session = Depends(get_db),
) -> EmployeeCrudService:
    """Returns EmployeeCrudService with fresh Unit of Work per request."""
    uow = HRUnitOfWork(session)
    return EmployeeCrudService(uow)


def get_staff_account_service(
    session: Session = Depends(get_db),
    supabase_client = Depends(get_supabase_admin),
) -> StaffAccountService:
    """Returns StaffAccountService with fresh Unit of Work per request."""
    uow = HRUnitOfWork(session)
    return StaffAccountService(uow, supabase_client)