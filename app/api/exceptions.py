"""
FastAPI exceptions handler mappings.
"""
import logging

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.shared.exceptions import (
    NotFoundError,
    ValidationError,
    BusinessRuleError,
    ConflictError,
    AuthError
)

logger = logging.getLogger("api.access")


def register_exception_handlers(app):
    @app.exception_handler(NotFoundError)
    async def not_found_exception_handler(request: Request, exc: NotFoundError):
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "NotFoundError", "message": exc.message},
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=422,
            content={"success": False, "error": "ValidationError", "message": exc.message},
        )

    @app.exception_handler(RequestValidationError)
    async def pydantic_validation_handler(request: Request, exc: RequestValidationError):
        """
        Handle Pydantic validation errors with standardized format.
        """
        errors = exc.errors()
        message = "; ".join([f"{e['loc']}: {str(e['msg'])}" for e in errors[:3]])
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": "ValidationError",
                "message": message,
                "details": [
                    {k: str(v) if not isinstance(v, (str, int, float, bool, list, dict, type(None))) else v
                     for k, v in err.items()}
                    for err in errors
                ]
            },
        )

    @app.exception_handler(BusinessRuleError)
    async def business_rule_exception_handler(request: Request, exc: BusinessRuleError):
        return JSONResponse(
            status_code=409,
            content={"success": False, "error": "BusinessRuleError", "message": exc.message},
        )

    @app.exception_handler(ConflictError)
    async def conflict_exception_handler(request: Request, exc: ConflictError):
        return JSONResponse(
            status_code=409,
            content={"success": False, "error": "ConflictError", "message": exc.message},
        )

    @app.exception_handler(AuthError)
    async def auth_exception_handler(request: Request, exc: AuthError):
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": "AuthError", "message": exc.message},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """
        Converts FastAPI HTTPException to standard ErrorResponse envelope.
        Preserves status code while unifying response format.
        """
        error_type_map = {
            400: "BadRequest",
            401: "Unauthorized",
            403: "Forbidden",
            404: "NotFound",
            405: "MethodNotAllowed",
            409: "Conflict",
            422: "ValidationError",
            500: "InternalServerError",
        }
        error_type = error_type_map.get(exc.status_code, "HTTPError")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": error_type,
                "message": exc.detail,
            },
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """Catch-all: log full traceback and return 500."""
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "InternalServerError",
                "message": "An unexpected error occurred. The server logs contain details.",
            },
        )
