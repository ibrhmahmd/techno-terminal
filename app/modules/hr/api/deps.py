"""HR HTTP-layer service factories (ADR-0002: api/ → services/)."""

from fastapi import Depends
from sqlmodel import Session
from app.api.dependencies import UoW, get_supabase_admin
from app.modules.hr import EmployeeCrudService, StaffAccountService


def get_employee_crud_service(
    uow: UoW,
) -> EmployeeCrudService:
    """Returns EmployeeCrudService with request-scoped UnitOfWork."""
    return EmployeeCrudService(uow)


def get_staff_account_service(
    uow: UoW,
    supabase_client = Depends(get_supabase_admin),
) -> StaffAccountService:
    """Returns StaffAccountService with request-scoped UnitOfWork."""
    return StaffAccountService(uow, supabase_client)