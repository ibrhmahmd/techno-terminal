"""
app/api/routers/competitions/__init__.py
──────────────────────────────────────
Competitions router package exports.
"""

from app.api.routers.competitions.competitions_router import router as competitions_router
from app.api.routers.competitions.teams_router import router as teams_router

__all__ = ["competitions_router", "teams_router"]
