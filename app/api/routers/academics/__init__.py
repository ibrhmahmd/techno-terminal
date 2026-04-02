"""
app/api/routers/academics/__init__.py
────────────────────────────────────
Academics routers package.

Exports all academics sub-routers for easy inclusion in main.py
"""
from app.api.routers.academics.courses import router as courses_router
from app.api.routers.academics.groups import router as groups_router
from app.api.routers.academics.sessions import router as sessions_router

__all__ = [
    "courses_router",
    "groups_router",
    "sessions_router",
]
