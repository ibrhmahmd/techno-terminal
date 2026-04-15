"""
Repository protocol interfaces.
"""
from .Ireceipt_repository import IReceiptRepository
from .Ipayment_repository import IPaymentRepository
from .Ireporting_repository import IReportingRepository

__all__ = [
    "IReceiptRepository",
    "IPaymentRepository",
    "IReportingRepository",
]
