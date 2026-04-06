"""
app/api/routers/academics/__init__.py
────────────────────────────────────
Academics routers package.

Exports all academics sub-routers for easy inclusion in main.py
"""
from app.api.routers.academics.courses_router import router as courses_router
from app.api.routers.academics.groups_router import router as groups_router
from app.api.routers.academics.sessions_router import router as sessions_router
from app.api.routers.academics.group_lifecycle_router import router as group_lifecycle_router
from app.api.routers.academics.group_competitions_router import router as group_competitions_router

__all__ = [
    "courses_router",
    "groups_router",
    "sessions_router",
    "group_lifecycle_router",
    "group_competitions_router"
]
