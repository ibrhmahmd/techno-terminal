"""
app/modules/finance/interfaces/dto/search_receipts_dto.py
───────────────────────────────────────────────────────────
Search receipts DTO.
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class SearchReceiptsDTO:
    """Parameters for searching receipts."""
    from_date: date
    to_date: date
    payer_name_contains: Optional[str] = None
    student_id: Optional[int] = None
    receipt_number_contains: Optional[str] = None
    limit: int = 200
