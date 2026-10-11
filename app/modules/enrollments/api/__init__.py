"""
app/modules/enrollments/api/__init__.py
──────────────────────────────────────
Enrollments HTTP layer (ADR-0002): routers, HTTP schemas, factories.

Exports the enrollments sub-routers for inclusion in main.py.
"""
from app.modules.enrollments.api.enrollments_router import (
    router as enrollments_router,
    progress_router as enrollments_progress_router,
)

__all__ = [
    "enrollments_router",
    "enrollments_progress_router",
]
