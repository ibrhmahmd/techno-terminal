"""
app/modules/finance/interfaces/dto/issue_refund_dto.py
────────────────────────────────────────────────────────
Issue refund DTO.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class IssueRefundDTO:
    """Parameters for issuing a refund."""
    payment_id: int
    amount: Decimal
    reason: str
    received_by_user_id: Optional[int]
    method: str = "cash"
