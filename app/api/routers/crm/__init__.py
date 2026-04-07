"""
app/api/routers/crm/__init__.py
───────────────────────────────
CRM routers package.

Exports all CRM sub-routers for easy inclusion in main.py
"""
from app.api.routers.crm.students import router as students_router
from app.api.routers.crm.parents import router as parents_router

__all__ = [
    "students_router",
    "parents_router",
]
