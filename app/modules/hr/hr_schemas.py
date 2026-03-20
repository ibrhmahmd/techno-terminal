from typing import Optional
from pydantic import BaseModel

class CreateEmployeeDTO(BaseModel):
    full_name: str
    phone: Optional[str] = None
    job_title: Optional[str] = None
    is_active: bool = True

class UpdateEmployeeDTO(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    is_active: Optional[bool] = None
