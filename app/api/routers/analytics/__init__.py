"""
app/api/routers/analytics/__init__.py
─────────────────────────────────────
Analytics routers package.

Exports all analytics sub-routers for easy inclusion in main.py
"""
from app.api.routers.analytics.academic import router as academic_router
from app.api.routers.analytics.financial import router as financial_router
from app.api.routers.analytics.competition import router as competition_router
from app.api.routers.analytics.bi import router as bi_router

__all__ = [
    "academic_router",
    "financial_router",
    "competition_router",
    "bi_router",
]









   
