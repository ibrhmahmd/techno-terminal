"""Competition fee payment DTOs (moved from competitions, ticket #34)."""
from typing import Optional

from pydantic import BaseModel


class PayCompetitionFeeInput(BaseModel):
    team_id: int
    student_id: int
    amount: float  # Payment amount (supports partial payments)
    parent_id: Optional[int] = None
    received_by_user_id: Optional[int] = None


class PayCompetitionFeeResponseDTO(BaseModel):
    """Returned by pay_competition_fee"""
    receipt_number: str
    payment_id: int
    amount: float
    amount_paid: float  # New running total after this payment
    amount_due: float  # For context
