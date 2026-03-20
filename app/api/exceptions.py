"""
FastAPI exceptions handler mappings.
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from app.shared.exceptions import (
    NotFoundError,
    ValidationError,
    BusinessRuleError,
    ConflictError,
    AuthError
)

def register_exception_handlers(app):
    @app.exception_handler(NotFoundError)
    async def not_found_exception_handler(request: Request, exc: NotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": exc.message, "error_type": "NotFoundError"},
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.message, "error_type": "ValidationError"},
        )

    @app.exception_handler(BusinessRuleError)
    async def business_rule_exception_handler(request: Request, exc: BusinessRuleError):
        return JSONResponse(
            status_code=409,  # 409 Conflict or 400 Bad Request
            content={"detail": exc.message, "error_type": "BusinessRuleError"},
        )

    @app.exception_handler(ConflictError)
    async def conflict_exception_handler(request: Request, exc: ConflictError):
        return JSONResponse(
            status_code=409,
            content={"detail": exc.message, "error_type": "ConflictError"},
        )

    @app.exception_handler(AuthError)
    async def auth_exception_handler(request: Request, exc: AuthError):
        return JSONResponse(
            status_code=401,
            content={"detail": exc.message, "error_type": "AuthError"},
            headers={"WWW-Authenticate": "Bearer"},
        )
