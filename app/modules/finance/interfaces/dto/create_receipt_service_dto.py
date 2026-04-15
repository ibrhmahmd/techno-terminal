"""
app/modules/finance/interfaces/dto/create_receipt_service_dto.py
──────────────────────────────────────────────────────────────────
Create receipt service DTO.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class CreateReceiptServiceDTO:
    """Parameters for ReceiptService.create()."""
    lines: List
    payer_name: Optional[str]
    payment_method: str
    received_by_user_id: Optional[int]
    allow_credit: bool = False
    notes: Optional[str] = None
