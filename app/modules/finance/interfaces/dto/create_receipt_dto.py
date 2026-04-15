"""
app/modules/finance/interfaces/dto/create_receipt_dto.py
───────────────────────────────────────────────────────────
Create receipt DTO.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CreateReceiptDTO:
    """Parameters for creating a receipt."""
    payer_name: Optional[str]
    payment_method: str
    received_by_user_id: Optional[int]
    notes: Optional[str] = None
