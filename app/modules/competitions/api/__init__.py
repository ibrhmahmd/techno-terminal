"""Competitions HTTP layer (ADR-0002)."""

from app.modules.competitions.api.competitions_router import router as competitions_router
from app.modules.competitions.api.teams_router import router as teams_router

__all__ = ["competitions_router", "teams_router"]
