"""
app/modules/auth/api/admin_auth_router.py
─────────────────────────────────────────
Admin user management + audit endpoints.

Prefix: /api/v1/admin  (mounted in main.py)
Tag:    Admin Auth
"""

import logging
from datetime import datetime, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_admin
from app.core.config import settings
from app.modules.auth.constants import UserRoleValue
from app.modules.auth.api.deps import get_auth_service, get_audit_service, get_auth_notifier
from app.api.schemas.common import ApiResponse, PaginatedResponse
from app.modules.auth.api.schemas import UpdateUserRequest, InviteUserRequest
from app.modules.auth import AuthService, AuditService, AuthNotifier, User, UserAdminDTO, InviteResultDTO, AuditLogEntryDTO

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin Auth"])


def _parse_audit_date(value: datetime | None) -> datetime | None:
    """Default a naive date/datetime query param to UTC.

    FastAPI has already parsed the ISO value (a bad one is a 422, #140).
    AuditLog.created_at is timezone-aware, so a naive value -- e.g. a bare
    date like "2026-09-01" -- would fail at query time.
    """
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=timezone.utc)


@router.get(
    "/users",
    response_model=PaginatedResponse[UserAdminDTO],
    summary="List all users",
)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: bool | None = None,
    role: UserRoleValue | None = None,
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
    summary="Delete user permanently",
)
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    auth_svc: AuthService = Depends(get_auth_service),
):
    auth_svc.delete_user(user_id, current_user)
    return ApiResponse(data=None, message="User deleted.")


@router.post(
    "/users/invite",
    response_model=ApiResponse[InviteResultDTO],
    summary="Invite a new user",
)
def invite_user(
    body: InviteUserRequest,
    _user: User = Depends(require_admin),
    auth_svc: AuthService = Depends(get_auth_service),
    notifier: AuthNotifier = Depends(get_auth_notifier),
):
    user = auth_svc.invite_user(email=body.email, role=body.role, employee_id=body.employee_id)
    data = InviteResultDTO.model_validate(user, from_attributes=True)

    # Email the registration link after commit (ADR-0007, #148); a failure
    # never undoes the invite.
    base_url = settings.frontend_base_url.rstrip("/")
    if not base_url:
        logger.warning("FRONTEND_BASE_URL is not set; invite for user %s was not emailed", user.id)
        return ApiResponse(
            data=data,
            message="Invite created, but no email was sent: FRONTEND_BASE_URL is not configured.",
        )
    try:
        notifier.user_invited(
            email=user.username,
            role=user.role,
            register_url=f"{base_url}/register?{urlencode({'token': user.invite_token})}",
            expires_at=user.invite_expires_at,
            employee_id=user.employee_id,
        )
    except Exception:
        logger.exception("AuthNotifier.user_invited failed; the invite stands")
    return ApiResponse(data=data, message=f"Invite created. The registration link is being emailed to {user.username}.")


@router.get(
    "/audit/logins",
    response_model=PaginatedResponse[AuditLogEntryDTO],
    summary="Login history",
)
def audit_logins(
    user_id: int | None = None,
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _user: User = Depends(require_admin),
    audit_svc: AuditService = Depends(get_audit_service),
):
    from_date_dt = _parse_audit_date(from_date)
    to_date_dt = _parse_audit_date(to_date)
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
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _user: User = Depends(require_admin),
    audit_svc: AuditService = Depends(get_audit_service),
):
    from_date_dt = _parse_audit_date(from_date)
    to_date_dt = _parse_audit_date(to_date)
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
    from_date: datetime = Query(..., alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _user: User = Depends(require_admin),
    audit_svc: AuditService = Depends(get_audit_service),
):
    from_date_dt = _parse_audit_date(from_date)
    to_date_dt = _parse_audit_date(to_date)
    result = audit_svc.query_failed_attempts(
        from_date=from_date_dt,
        to_date=to_date_dt,
        skip=skip,
        limit=limit,
    )
    return PaginatedResponse(data=result.items, total=result.total, skip=skip, limit=limit)
