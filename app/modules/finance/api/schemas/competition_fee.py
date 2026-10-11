"""
app/api/schemas/finance/competition_fee.py
──────────────────────────────────────────
HTTP request bodies for the competition fee endpoints (moved from competitions, #34).
"""
from typing import Optional

from pydantic import BaseModel, Field


class PayCompetitionFeeBody(BaseModel):
    """Input for paying a competition fee for a team member."""
    amount: float = Field(..., gt=0, description="Payment amount")
    parent_id: Optional[int] = None


class RefundCompetitionFeeBody(BaseModel):
    """Input for refunding a competition fee payment."""
    amount: float = Field(..., gt=0, description="Refund amount (must be <= current amount_paid)")
