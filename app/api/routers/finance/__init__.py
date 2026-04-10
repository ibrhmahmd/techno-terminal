"""
app/api/routers/crm/__init__.py
───────────────────────────────
CRM routers package.

Exports all CRM sub-routers for easy inclusion in main.py
"""
from app.api.routers.finance.balance_router import router as balance_router
from app.api.routers.finance.finance_router import router as finance_router
from app.api.routers.finance.receipt_router import router as receipt_router

__all__ = [
    "balance_router",
    "finance_router",
    "receipt_router",
]
