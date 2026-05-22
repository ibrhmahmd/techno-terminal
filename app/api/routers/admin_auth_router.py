"""
app/api/routers/admin_auth_router.py
────────────────────────────────────
Admin user management + audit endpoints.

Prefix: /api/v1/admin  (mounted in main.py)
Tag:    Admin Auth
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import require_admin, get_auth_service, get_audit_service
from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.api.schemas.auth import UpdateUserRequest, InviteUserRequest
from app.modules.auth import AuthService, AuditService, User, UserAdminDTO, InviteResultDTO, AuditLogEntryDTO

router = APIRouter(tags=["Admin Auth"])


@router.get(
    "/users",
    response_model=PaginatedResponse[UserAdminDTO],
    summary="List all users",
)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: bool | None = None,
    role: str | None = None,
    q: str | None = None,
    _user: User = Depends(require_admin),
    auth_svc: AuthService = Depends(get_auth_service),
):
    result = auth_svc.list_users(skip=skip, limit=limit, is_active=is_active, role=role, q=q)
    return PaginatedResponse(
        data=[UserAdminDTO.model_validate(u, from_attributes=True) for u in result.items],
        total=result.total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/users/{user_id}",
    response_model=ApiResponse[UserAdminDTO],
    summary="Get user by ID",
)
def get_user(
    user_id: int,
    _user: User = Depends(require_admin),
    auth_svc: AuthService = Depends(get_auth_service),
):
    user = auth_svc.get_user(user_id)
    return ApiResponse(data=UserAdminDTO.model_validate(user, from_attributes=True))


@router.patch(
    "/users/{user_id}",
    response_model=ApiResponse[UserAdminDTO],
    summary="Update user role or active status",
)
def update_user(
    user_id: int,
    body: UpdateUserRequest,
    current_user: User = Depends(require_admin),
    auth_svc: AuthService = Depends(get_auth_service),
):
    updated = auth_svc.update_user(user_id, body, current_user)
    return ApiResponse(
        data=UserAdminDTO.model_validate(updated, from_attributes=True),
        message="User updated.",
    )


@router.delete(
    "/users/{user_id}",
    response_model=ApiResponse[None],
    summary="Deactivate user",
)
def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    auth_svc: AuthService = Depends(get_auth_service),
):
    auth_svc.deactivate_user(user_id, current_user)
    return ApiResponse(data=None, message="User deactivated.")


@router.post(
    "/users/invite",
    response_model=ApiResponse[InviteResultDTO],
    summary="Invite a new user",
)
def invite_user(
    body: InviteUserRequest,
    _user: User = Depends(require_admin),
    auth_svc: AuthService = Depends(get_auth_service),
):
    user = auth_svc.invite_user(email=body.email, role=body.role, employee_id=body.employee_id)
    return ApiResponse(
        data=InviteResultDTO.model_validate(user, from_attributes=True),
        message="Invite sent.",
    )


@router.get(
    "/audit/logins",
    response_model=PaginatedResponse[AuditLogEntryDTO],
    summary="Login history",
)
def audit_logins(
    user_id: int | None = None,
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _user: User = Depends(require_admin),
    audit_svc: AuditService = Depends(get_audit_service),
):
    from_date_dt = datetime.fromisoformat(from_date) if from_date else None
    to_date_dt = datetime.fromisoformat(to_date) if to_date else None
    result = audit_svc.query_logins(
        user_id=user_id,
        from_date=from_date_dt,
        to_date=to_date_dt,
        skip=skip,
        limit=limit,
    )
    return PaginatedResponse(data=result.items, total=result.total, skip=skip, limit=limit)


@router.get(
    "/audit/password-changes",
    response_model=PaginatedResponse[AuditLogEntryDTO],
    summary="Password change log",
)
def audit_password_changes(
    user_id: int | None = None,
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _user: User = Depends(require_admin),
    audit_svc: AuditService = Depends(get_audit_service),
):
    from_date_dt = datetime.fromisoformat(from_date) if from_date else None
    to_date_dt = datetime.fromisoformat(to_date) if to_date else None
    result = audit_svc.query_password_changes(
        user_id=user_id,
        from_date=from_date_dt,
        to_date=to_date_dt,
        skip=skip,
        limit=limit,
    )
    return PaginatedResponse(data=result.items, total=result.total, skip=skip, limit=limit)


@router.get(
    "/audit/failed-attempts",
    response_model=PaginatedResponse[AuditLogEntryDTO],
    summary="Failed login attempts",
)
def audit_failed_attempts(
    from_date: str = Query(..., alias="from"),
    to_date: str | None = Query(None, alias="to"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _user: User = Depends(require_admin),
    audit_svc: AuditService = Depends(get_audit_service),
):
    from_date_dt = datetime.fromisoformat(from_date)
    to_date_dt = datetime.fromisoformat(to_date) if to_date else None
    result = audit_svc.query_failed_attempts(
        from_date=from_date_dt,
        to_date=to_date_dt,
        skip=skip,
        limit=limit,
    )
    return PaginatedResponse(data=result.items, total=result.total, skip=skip, limit=limit)
