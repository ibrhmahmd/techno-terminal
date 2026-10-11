from datetime import datetime
from typing import Optional
from decimal import Decimal

from pydantic import BaseModel


class EnrollmentHistoryDTO(BaseModel):
    id: int
    student_id: int
    enrollment_id: Optional[int]
    group_id: Optional[int]
    group_name: Optional[str]
    level_number: Optional[int]
    enrollment_status: Optional[str]
    amount_due: Optional[Decimal]
    discount_applied: Optional[Decimal]
    action: str
    action_date: datetime
    previous_group_id: Optional[int]
    previous_level_number: Optional[int]
    previous_status: Optional[str]
    transfer_reason: Optional[str]
    performed_by: Optional[int]
    performed_by_name: Optional[str]
    notes: Optional[str]

    model_config = {"frozen": True}
