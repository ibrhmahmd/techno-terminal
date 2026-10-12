"""
app/modules/audit/api/router.py
───────────────────────────────
Integrity checks (scenarios A–I): the anomalies the audit views detect. Admin-only, read-only.
"""
from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_admin
from app.api.schemas.common import ApiResponse, ErrorResponse, PaginatedResponse
from app.modules.audit.api.deps import get_audit_service
from app.modules.audit.schemas import AuditRowDTO, AuditScenarioDTO
from app.modules.audit.services import AuditService
from app.modules.auth import User

router = APIRouter(
    tags=["Audit"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
    },
)


@router.get(
    "/audit/scenarios",
    response_model=ApiResponse[list[AuditScenarioDTO]],
    summary="List the integrity checks with their anomaly counts",
)
def list_audit_scenarios(
    _user: User = Depends(require_admin),
    svc: AuditService = Depends(get_audit_service),
):
    """Scenarios A–I, errors first, then warnings, then info."""
    return ApiResponse(data=svc.list_scenarios())


@router.get(
    "/audit/scenarios/{code}",
    response_model=PaginatedResponse[AuditRowDTO],
    summary="List the anomalies one integrity check found",
    responses={404: {"model": ErrorResponse, "description": "Unknown scenario"}},
)
def list_audit_scenario_rows(
    code: str,
    since: date | None = Query(None, description="Only rows dated on or after this day (ignored by checks without a date)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    _user: User = Depends(require_admin),
    svc: AuditService = Depends(get_audit_service),
):
    """The rows of one check (A–I); the row shape depends on the check."""
    result = svc.get_scenario_rows(code, since=since, skip=skip, limit=limit)
    return PaginatedResponse(data=result.rows, total=result.total, skip=skip, limit=limit)
