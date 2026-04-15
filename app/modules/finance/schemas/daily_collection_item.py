"""
app/modules/finance/schemas/daily_collection_item.py
──────────────────────────────────────────────────────
Daily collection item schema.
"""
from datetime import date
from pydantic import BaseModel


class DailyCollectionItem(BaseModel):
    """Daily collection summary by payment method."""

    payment_method: str
    total_amount: float
    receipt_count: int
    target_date: date

    model_config = {"from_attributes": True}
