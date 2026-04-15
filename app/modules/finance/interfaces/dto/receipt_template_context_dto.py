"""
app/modules/finance/interfaces/dto/receipt_template_context_dto.py
───────────────────────────────────────────────────────────────────
Receipt template context DTO.
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.modules.crm.models.student_models import Student
    from app.modules.finance.models import Receipt


@dataclass(frozen=True)
class ReceiptTemplateContextDTO:
    """Context for receipt template rendering."""
    receipt: "Receipt"
    student: Optional["Student"]
    lines: list
    total: float
