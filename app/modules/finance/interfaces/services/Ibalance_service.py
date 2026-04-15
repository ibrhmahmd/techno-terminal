"""
Balance service protocol.
"""
from typing import List, Optional, Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.finance.interfaces.dto import OverpaymentRiskItem
    from app.modules.finance.schemas import EnrollmentBalanceItem


@runtime_checkable
class IBalanceService(Protocol):
    """Protocol for balance calculation operations."""

    def get_enrollment_balance(
        self, enrollment_id: int
    ) -> Optional["EnrollmentBalanceItem"]: ...

    def get_student_balances(
        self, student_id: int
    ) -> List["EnrollmentBalanceItem"]: ...

    def assess_overpayment_risk(
        self, lines
    ) -> List["OverpaymentRiskItem"]: ...
