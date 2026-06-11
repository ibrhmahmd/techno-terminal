from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class LogPaymentDTO(BaseModel):
    student_id: int
    payment_id: int
    amount: Decimal
    payment_type: str
    performed_by: Optional[int] = None
    metadata: Optional[dict] = None

    model_config = {"frozen": True}
