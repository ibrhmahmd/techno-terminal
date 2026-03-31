"""
app/api/schemas/common.py
─────────────────────────
Shared response envelopes used by every API endpoint.

Every successful response is wrapped in ApiResponse or PaginatedResponse.
Every error is wrapped by ErrorResponse (auto-emitted by exceptions.py).

Usage:
    @router.get("/students/{id}", response_model=ApiResponse[StudentPublic])
    def get_student(...):
        student = svc.get_student_by_id(id)
        return ApiResponse(data=StudentPublic.model_validate(student))
"""
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    Standard single-item success envelope.

    JSON shape:
        { "success": true, "data": {...}, "message": null }
    """

    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard list/paginated success envelope.

    JSON shape:
        { "success": true, "data": [...], "total": 42, "skip": 0, "limit": 50 }
    """

    success: bool = True
    data: list[T]
    total: int
    skip: int = 0
    limit: int = 50


class ErrorResponse(BaseModel):
    """
    Standard error envelope — emitted automatically by exceptions.py handlers.
    Documented here so OpenAPI generates the correct error schema.

    JSON shape:
        { "success": false, "error": "NotFoundError", "message": "Student 12 not found" }
    """

    success: bool = False
    error: str    # machine-readable type e.g. "NotFoundError", "ConflictError"
    message: str  # human-readable detailstring
