"""
app/modules/finance/schemas/daily_receipt_item.py
──────────────────────────────────────────────────
Daily receipt item schema.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DailyReceiptItem(BaseModel):
    """Receipt summary for daily reporting."""

    receipt_id: int
    receipt_number: str
    payer_name: Optional[str]
    total_amount: float
    payment_method: str
    issued_at: datetime

    model_config = {"from_attributes": True}
