"""
Techno Terminal - FastAPI Application Factory
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.exceptions import register_exception_handlers
from app.api.middleware.logging_middleware import logging_middleware
from app.api.routers import auth_router
from app.api.routers import attendance_router
from app.api.routers import enrollments_router
from app.api.routers import competitions_router
from app.api.routers import hr_router
from app.api.routers.crm import (
    students_router,
    parents_router,
    students_history_router,
)
from app.api.routers.academics import (
    courses_router,
    groups_router,
    sessions_router,
    group_lifecycle_router,
    group_competitions_router,
)
from app.api.routers.analytics import (
    academic_router,
    financial_router,
    competition_router,
    bi_router,
)
from app.api.routers.finance import (
    balance_router,
    receipt_router,
    finance_router

)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Techno Terminal API",
        description="RESTful backend for the Techno Terminal CRM & Operations System",
        version="1.0.0",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        openapi_url="/api/v1/openapi.json",
    )

    # 1. Access logger (runs first — outermost wrapper)
    app.add_middleware(BaseHTTPMiddleware, dispatch=logging_middleware)

    # 2. CORS — open for development; tighten per-environment before public deploy
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 3. Global domain exception → HTTP status mappings
    register_exception_handlers(app)

    # 4. Routers
    app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["Authentication"])
    # Phase 5.2 — CRM (split into Students and Parents)
    app.include_router(students_router, prefix="/api/v1", tags=["CRM — Students"])
    app.include_router(parents_router,   prefix="/api/v1", tags=["CRM — Parents"])
    # Phase 5.3 — Academics (split into Courses, Groups, Sessions) + Attendance
    app.include_router(courses_router,  prefix="/api/v1", tags=["Academics — Courses"])
    app.include_router(groups_router,    prefix="/api/v1", tags=["Academics — Groups"])
    app.include_router(sessions_router,  prefix="/api/v1", tags=["Academics — Sessions"])
    app.include_router(group_lifecycle_router, prefix="/api/v1", tags=["Academics — Group Lifecycle"])
    app.include_router(group_competitions_router, prefix="/api/v1", tags=["Academics — Group Competitions"])
    app.include_router(attendance_router.router, prefix="/api/v1", tags=["Attendance"])
    # Phase 5.4 — Transactions
    app.include_router(enrollments_router.router, prefix="/api/v1", tags=["Enrollments"])
    # Finance routers (balance and receipt are already APIRouter objects)
    app.include_router(balance_router,     prefix="/api/v1", tags=["Student Balance"])
    app.include_router(receipt_router,     prefix="/api/v1", tags=["Receipts"])
    # Student History & Activity
    app.include_router(students_history_router,     prefix="/api/v1", tags=["Student History"])
    # Phase 5.5 — Auxiliary
    app.include_router(competitions_router.router, prefix="/api/v1", tags=["Competitions"])
    app.include_router(hr_router.router,           prefix="/api/v1", tags=["HR"])
    # Analytics (split into 4 sub-domains)
    app.include_router(academic_router,    prefix="/api/v1", tags=["Analytics — Academic"])
    app.include_router(financial_router,   prefix="/api/v1", tags=["Analytics — Financial"])
    app.include_router(competition_router, prefix="/api/v1", tags=["Analytics — Competition"])
    app.include_router(bi_router,          prefix="/api/v1", tags=["Analytics — BI"])

    # 5. Utility endpoints
    @app.get("/health", tags=["Health"])
    def health_check():
        return {"status": "ok", "service": "Techno Terminal API", "version": "1.0.0"}

    return app


app = create_app()
