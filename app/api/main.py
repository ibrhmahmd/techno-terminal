"""
Techno Kids CRM - FastAPI Application Factory
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.exceptions import register_exception_handlers

from app.api.routers import auth
# from app.api.routers import crm, academics, enrollments, finance, analytics


def create_app() -> FastAPI:
    app = FastAPI(
        title="Techno Future API",
        description="RESTful backend for the Techno Future CRM",
        version="1.0.0",
    )

    # 1. Mount CORS (Currently completely open for development)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Register Global Exception Handlers
    register_exception_handlers(app)

    # 3. Mount Routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    # app.include_router(crm.router, prefix="/api/v1/crm", tags=["CRM"])

    @app.get("/health")
    def health_check():
        return {"status": "ok", "message": "Techno Future API is running"}

    return app


app = create_app()
