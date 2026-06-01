from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class GroupRosterEntryDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    enrollment_id: int
    student_id: int
    student_name: str
    billing_status: str
    balance: float
    joined_at: Optional[datetime] = None


class GroupEnrollmentDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    enrollment_id: int
    student_id: int
    student_name: str
    student_phone: Optional[str] = None
    parent_name: Optional[str] = None
    level_number: int
    status: str
    enrolled_at: Optional[datetime] = None
    sessions_attended: int
    sessions_total: int
    payment_status: str
    amount_due: float
    amount_paid: float
    discount_applied: float
    can_transfer: bool
    can_drop: bool
