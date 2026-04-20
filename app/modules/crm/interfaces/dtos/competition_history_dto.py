"""
app/modules/crm/interfaces/dtos/competition_history_dto.py
────────────────────────────────────────────────────────────
DTO for competition participation history entries.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal


@dataclass(frozen=True)
class CompetitionHistoryDTO:
    """Immutable DTO for competition participation history."""
    
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
