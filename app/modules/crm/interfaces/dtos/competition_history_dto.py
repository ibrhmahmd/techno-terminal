from datetime import datetime
from typing import Optional
from decimal import Decimal

from pydantic import BaseModel


class CompetitionHistoryDTO(BaseModel):
    id: int
    student_id: int
    competition_id: int
    competition_name: Optional[str]
    team_id: Optional[int]
    team_name: Optional[str]
    participation_type: str
    registration_date: Optional[datetime]
    subscription_amount: Optional[Decimal]
    subscription_paid: Optional[bool]
    payment_id: Optional[int]
    result_position: Optional[int]
    result_notes: Optional[str]
    performed_by: Optional[int]
    performed_by_name: Optional[str]
    created_at: datetime

    model_config = {"frozen": True}
