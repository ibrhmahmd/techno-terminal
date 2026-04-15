"""
app/modules/finance/schemas/receipt_search_item.py
────────────────────────────────────────────────────
Receipt search item schema.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ReceiptSearchItem(BaseModel):
    """Receipt search result item."""

    id: int
    receipt_number: Optional[str]
    payer_name: Optional[str]
    payment_method: str
    paid_at: datetime

    model_config = {"from_attributes": True}
