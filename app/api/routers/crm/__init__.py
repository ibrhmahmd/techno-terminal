"""
app/api/routers/crm/__init__.py
───────────────────────────────
CRM routers package.

Exports all CRM sub-routers for easy inclusion in main.py
"""
from app.api.routers.crm.students_router import router as students_router
from app.api.routers.crm.parents_router import router as parents_router
from app.api.routers.crm.students_history_router import router as students_history_router

__all__ = [
    "students_router",
    "parents_router",
    "students_history_router",
]
