"""

app/modules/crm/schemas/student_schemas.py
───────────────────────────────────────────

Pydantic DTOs scoped to Student operations.
"""
from datetime import date

from typing import Optional


from pydantic import BaseModel



class RegisterStudentDTO(BaseModel):
    """

    Input for CRMService.register_student().

    Streamlit date_input returns datetime.date; APIs may send ISO date strings.
    """
    full_name: str

    date_of_birth: Optional[date] = None

    gender: Optional[str] = None  # 'male' | 'female'

    phone: Optional[str] = None

    notes: Optional[str] = None



class UpdateStudentDTO(BaseModel):
    """

    Input for CRMService.update_student().

    All fields are optional; only provided fields will be written.
    """

    full_name: Optional[str] = None

    date_of_birth: Optional[date] = None

    gender: Optional[str] = None

    phone: Optional[str] = None

    notes: Optional[str] = None

    is_active: Optional[bool] = None


class RegisterStudentCommandDTO(BaseModel):
    """

    Unified command DTO encompassing the student payload, parent relationship,

    and audit context for full CQRS-style registration.
    """

    student_data: RegisterStudentDTO

    parent_id: Optional[int] = None

    relationship: Optional[str] = None

    created_by_user_id: Optional[int] = None

