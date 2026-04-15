"""
Refund service protocol.
"""
from typing import Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.finance.interfaces.dto import (
        RefundResultDTO,
        IssueRefundDTO,
    )


@runtime_checkable
class IRefundService(Protocol):
    """Protocol for refund business operations."""

    def issue(self, dto: "IssueRefundDTO") -> "RefundResultDTO": ...
