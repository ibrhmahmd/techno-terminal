"""
app/api/routers/analytics/__init__.py
─────────────────────────────────────
Analytics routers package.

Exports all analytics sub-routers for easy inclusion in main.py
"""
from app.modules.analytics.api.academic_router import router as academic_router
from app.modules.analytics.api.financial_router import router as financial_router
from app.modules.analytics.api.competition_router import router as competition_router
from app.modules.analytics.api.bi_router import router as bi_router
from app.modules.analytics.api.dashboard_router import router as dashboard_router

__all__ = [
    "academic_router",
    "financial_router",
    "competition_router",
    "bi_router",
    "dashboard_router",
]









   
