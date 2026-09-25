"""Protocol interface for scheduled report delivery claims."""
from datetime import date
from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class ReportDeliveryLedgerInterface(Protocol):
    def claim(
        self,
        template_id: int,
        period_start: date,
        recipient_type: str,
        recipient_id: int,
        recipient_contact: str,
        subject: Optional[str],
        body: str,
    ) -> Optional[int]: ...

    def mark(self, log_id: int, status: str, error_message: Optional[str]) -> None: ...
