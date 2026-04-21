"""
app/modules/finance/interfaces/dto/send_receipt_result_dto.py
────────────────────────────────────────────────────────────
Send receipt result DTO.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class SendReceiptResultDTO:
    """Immutable DTO for receipt sending operation result."""
    success: bool
    message: str
    receipt_id: int
    recipient_contact: Optional[str]  # phone or email used
    sent_at: datetime
