from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.exceptions import register_exception_handlers
from app.api.middleware.logging_middleware import logging_middleware
from app.api.routers import auth_router
from app.api.routers import attendance_router
from app.api.routers import enrollments_router
from app.api.routers.notifications import router as notifications_router
from app.api.routers.competitions import competitions_router, teams_router
from app.api.routers import hr_router
from app.api.routers.crm import (
    students_router,
    parents_router,
    students_history_router,
)
from app.api.routers.academics import (
    courses_router,
    groups_router,
    group_directory_router,
    sessions_router,
    group_lifecycle_router,
    group_competitions_router,
    group_details_router,
)
from app.api.routers.analytics import (
    academic_router,
    financial_router,
    competition_router,
    bi_router,
    dashboard_router,
)
from app.api.routers.finance import receipt_router, finance_router, reporting_router


def create_app() -> FastAPI:
    from app.db.connection import get_engine
    from sqlmodel import Session
    from app.modules.notifications.repositories.notification_repository import (
        NotificationRepository,
    )
    from app.modules.notifications.services.notification_service import (
        NotificationService,
    )
    from app.modules.notifications.services.report_scheduler import (
        start_report_scheduler,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        session = Session(get_engine(), expire_on_commit=False)
        notification_service = NotificationService(repo=NotificationRepository(session))
        task = asyncio.create_task(start_report_scheduler(notification_service))
        yield
        task.cancel()
        session.close()

    app = FastAPI(
        title="Techno Terminal API",
        description="RESTful backend for the Techno Terminal CRM & Operations System",
        version="1.0.0",
        lifespan=lifespan,
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
    app.include_router(
        auth_router.router, prefix="/api/v1/auth", tags=["Authentication"]
    )
    # CRM (Students and Parents)
    app.include_router(students_router, prefix="/api/v1", tags=["CRM — Students"])
    app.include_router(parents_router, prefix="/api/v1", tags=["CRM — Parents"])
    # Academics (Courses, Groups, Sessions) + Attendance
    app.include_router(courses_router, prefix="/api/v1", tags=["Academics — Courses"])
    app.include_router(groups_router, prefix="/api/v1", tags=["Academics — Groups"])
    app.include_router(
        group_directory_router, prefix="/api/v1", tags=["Academics — Group Directory"]
    )
    app.include_router(sessions_router, prefix="/api/v1", tags=["Academics — Sessions"])
    app.include_router(
        group_details_router, prefix="/api/v1", tags=["Academics — Group Details"]
    )
    app.include_router(
        group_lifecycle_router, prefix="/api/v1", tags=["Academics — Group Lifecycle"]
    )
    app.include_router(
        group_competitions_router,
        prefix="/api/v1",
        tags=["Academics — Group Competitions"],
    )
    app.include_router(attendance_router.router, prefix="/api/v1", tags=["Attendance"])
    # Transactions
    app.include_router(
        enrollments_router.router, prefix="/api/v1", tags=["Enrollments"]
    )
    # Finance routers (Receipts, Finance, Finance — Reporting)
    app.include_router(receipt_router, prefix="/api/v1", tags=["Receipts"])
    app.include_router(finance_router, prefix="/api/v1", tags=["Finance"])
    app.include_router(reporting_router, prefix="/api/v1", tags=["Finance — Reporting"])
    # Student History & Activity
    app.include_router(
        students_history_router, prefix="/api/v1", tags=["Student History"]
    )
    # Competitions (competitions and teams)
    app.include_router(competitions_router, prefix="/api/v1", tags=["Competitions"])
    app.include_router(teams_router, prefix="/api/v1", tags=["Teams"])
    # HR
    app.include_router(hr_router.router, prefix="/api/v1", tags=["HR"])
    # Analytics
    app.include_router(academic_router, prefix="/api/v1", tags=["Analytics — Academic"])
    app.include_router(
        financial_router, prefix="/api/v1", tags=["Analytics — Financial"]
    )
    app.include_router(
        competition_router, prefix="/api/v1", tags=["Analytics — Competition"]
    )
    app.include_router(bi_router, prefix="/api/v1", tags=["Analytics — BI"])
    app.include_router(
        dashboard_router, prefix="/api/v1", tags=["Analytics — Dashboard"]
    )

    # Notifications
    app.include_router(notifications_router, prefix="/api/v1")

    # 5. Utility endpoints
    @app.get("/health", tags=["Health"])
    def health_check():
        return {"status": "ok", "service": "Techno Terminal API"}

    # Leapcell platform health check endpoint
    @app.get("/kaithhealthcheck", tags=["Health"])
    def leapcell_health_check():
        return {"status": "ok"}

    return app


app = create_app()
