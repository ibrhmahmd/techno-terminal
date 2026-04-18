"""
app/api/routers/finance/__init__.py
───────────────────────────────────
Finance routers package.

Exports finance sub-routers for easy inclusion in main.py.
"""
from app.api.routers.finance.finance_router import router as finance_router
from app.api.routers.finance.receipt_router import router as receipt_router
from app.api.routers.finance.reporting_router import router as reporting_router

__all__ = [
    "finance_router",
    "receipt_router",
    "reporting_router",
]
