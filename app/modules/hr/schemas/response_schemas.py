"""Response Schemas

DTOs for paginated and list responses.
"""
from pydantic import BaseModel, ConfigDict

from .employee_schemas import EmployeeReadDTO


class EmployeeListResponseDTO(BaseModel):
    """Paginated employee list response."""
    model_config = ConfigDict(frozen=True)

    items: list[EmployeeReadDTO]
    total: int
    page: int
    page_size: int
