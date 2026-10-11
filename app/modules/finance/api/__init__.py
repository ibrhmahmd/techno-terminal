"""Finance HTTP layer (ADR-0002)."""

from app.modules.finance.api.competition_fees_router import router as competition_fees_router
from app.modules.finance.api.finance_router import router as finance_router
from app.modules.finance.api.receipt_router import router as receipt_router
from app.modules.finance.api.reporting_router import router as reporting_router
from app.modules.finance.api.student_payments_router import router as student_payments_router

__all__ = [
    "competition_fees_router",
    "finance_router",
    "receipt_router",
    "reporting_router",
    "student_payments_router",
]
