"""Finance module ports (ADR-0007)."""

from decimal import Decimal
from typing import Protocol


class PaymentNotifier(Protocol):
    """Port for payment notifications, called after the use case commits.

    Implementations must not raise; the caller logs and swallows failures.
    """

    def payment_received(
        self, *, receipt_id: int, student_id: int, amount: str, receipt_number: str
    ) -> None: ...

    def competition_fee_paid(
        self,
        *,
        student_id: int,
        team_id: int,
        team_name: str,
        competition_name: str,
        amount: Decimal,
        receipt_number: str,
    ) -> None: ...
