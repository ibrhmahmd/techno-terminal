"""
Techno Terminal - FastAPI Application Factory
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.exceptions import register_exception_handlers
from app.api.middleware.logging_middleware import logging_middleware
from app.api.routers import auth
from app.api.routers import crm
from app.api.routers import academics
from app.api.routers import attendance
# Domain routers — uncommented as each phase is implemented:
# from app.api.routers import enrollments
# from app.api.routers import finance
# from app.api.routers import competitions
# from app.api.routers import hr
# from app.api.routers import analytics


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
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    # Phase 5.2 — CRM
    app.include_router(crm.router, prefix="/api/v1", tags=["CRM"])
    # Phase 5.3 — Academics + Attendance
    app.include_router(academics.router,  prefix="/api/v1", tags=["Academics"])
    app.include_router(attendance.router, prefix="/api/v1", tags=["Attendance"])
    # Phase 5.4 — Transactions
    # app.include_router(enrollments.router, prefix="/api/v1", tags=["Enrollments"])
    # app.include_router(finance.router,     prefix="/api/v1", tags=["Finance"])
    # Phase 5.5 — Auxiliary
    # app.include_router(competitions.router, prefix="/api/v1", tags=["Competitions"])
    # app.include_router(hr.router,           prefix="/api/v1", tags=["HR"])
    # app.include_router(analytics.router,    prefix="/api/v1", tags=["Analytics"])

    # 5. Utility endpoints
    @app.get("/health", tags=["Health"])
    def health_check():
        return {"status": "ok", "service": "Techno Terminal API", "version": "1.0.0"}

    return app


app = create_app()
