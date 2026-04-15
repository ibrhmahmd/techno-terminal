"""
app/modules/finance/schemas/receipt_line_input.py
──────────────────────────────────────────────
Receipt line input schema.
"""
from typing import Optional
from pydantic import BaseModel, field_validator
from app.shared.validators import validate_positive_amount


class ReceiptLineInput(BaseModel):
    """One charge line for creating a receipt with payment lines."""

    student_id: int
    enrollment_id: Optional[int] = None
    team_member_id: Optional[int] = None
    amount: float
    payment_type: str = "course_level"
    discount: float = 0.0
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        validate_positive_amount(v, field="amount")
        return v
