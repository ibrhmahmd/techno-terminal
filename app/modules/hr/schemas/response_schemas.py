"""Response Schemas

DTOs for paginated and list responses.
"""
from pydantic import BaseModel, ConfigDict

from app.modules.hr.models import Employee
from .employee_schemas import EmployeeReadDTO


class EmployeeListResult(BaseModel):
    """Repository-level pagination result (ORM rows + total count)."""
    model_config = ConfigDict(frozen=True)

    items: list[Employee]
    total: int


class EmployeeListResponseDTO(BaseModel):
    """Paginated employee list response."""
    model_config = ConfigDict(frozen=True)

    items: list[EmployeeReadDTO]
    total: int
    page: int
    page_size: int
