"""
Payment repository protocol.
"""
from decimal import Decimal
from typing import List, Optional, Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.finance.models import Payment
    from app.modules.finance.interfaces.dto import (
        EnrollmentBalanceDTO,
        AddPaymentLineDTO,
    )
    from app.modules.finance.schemas import EnrollmentBalanceItem


@runtime_checkable
class IPaymentRepository(Protocol):
    """Protocol for payment data access operations."""

    def add_line(self, dto: "AddPaymentLineDTO") -> "Payment": ...

    def get_by_id(self, payment_id: int) -> Optional["Payment"]: ...

    def get_total_refunded(self, original_payment_id: int) -> Decimal: ...

    def get_enrollment_balance(
        self, enrollment_id: int
    ) -> Optional["EnrollmentBalanceDTO"]: ...

    def get_student_balances(
        self, student_id: int
    ) -> List["EnrollmentBalanceItem"]: ...
