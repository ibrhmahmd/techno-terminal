"""
app/modules/academics/api/__init__.py
────────────────────────────────────
Academics HTTP layer (ADR-0002): routers, HTTP schemas, factories.

Exports all academics sub-routers for easy inclusion in main.py
"""
from app.modules.academics.api.courses_router import router as courses_router
from app.modules.academics.api.groups_router import router as groups_router
from app.modules.academics.api.group_directory_router import router as group_directory_router
from app.modules.academics.api.sessions_router import router as sessions_router
from app.modules.academics.api.group_lifecycle_router import router as group_lifecycle_router
from app.modules.academics.api.group_details_router import router as group_details_router

__all__ = [
    "courses_router",
    "groups_router",
    "group_directory_router",
    "sessions_router",
    "group_lifecycle_router",
    "group_details_router",
]