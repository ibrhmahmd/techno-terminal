"""
app/api/routers/auth.py
────────────────────────
Authentication endpoints.

Prefix: /api/v1/auth  (mounted in main.py)
Tag:    Authentication

Phase 0 (done): GET /me — identity check for any valid JWT.
Phase 1 (done): Role enforcement via require_admin / require_any in dependencies.py.

All tokens are issued by Supabase. Use "Authorize" in Swagger UI with:
    Bearer <your_supabase_access_token>
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.schemas.common import ApiResponse
from app.modules.auth import AuthService, User, UserPublic, UserSessionDTO
from app.modules.auth.models.audit_log import AuditLogEventType
from app.modules.auth.services.audit_service import AuditService
from app.api.dependencies import get_current_user, require_admin, get_auth_service, get_audit_service
from app.modules.auth.schemas.auth_schemas import UpdateProfileInput
from app.api.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    CreateUserRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    UpdateProfileRequest,
    RegisterUserRequest,
)

from app.core.supabase_clients import get_supabase_anon

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])
http_bearer = HTTPBearer(auto_error=False)


# login
@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    summary="Login with Email and Password",
)
def login(
    body: LoginRequest,
    auth_svc: AuthService = Depends(get_auth_service),
):
    supabase = get_supabase_anon()
    try:
        res = supabase.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
        if not res.session:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception:
        AuditService().log_event(
            event_type=AuditLogEventType.LOGIN_FAILURE,
            details={"email": body.email},
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # verify against local DB
    user = auth_svc.get_user_by_supabase_uid(res.user.id)
    if not user:
        AuditService().log_event(
            event_type=AuditLogEventType.LOGIN_FAILURE,
            details={"supabase_uid": res.user.id, "reason": "no local identity"},
        )
        raise HTTPException(
            status_code=401, detail="User authenticated but no local identity found."
        )

    # stamp last login
    auth_svc.update_last_login(user.id)
    AuditService().log_event(
        event_type=AuditLogEventType.LOGIN_SUCCESS,
        user_id=user.id,
    )

    return ApiResponse(
        data=TokenResponse(
            access_token=res.session.access_token,
            refresh_token=res.session.refresh_token,
            user=UserPublic.model_validate(user, from_attributes=True),
        ),
        message="Login successful.",
    )


# refresh token
@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse],
    summary="Refresh Supabase JWT",
)
def refresh_token(
    body: RefreshRequest,
    auth_svc: AuthService = Depends(get_auth_service),
):
    supabase = get_supabase_anon()
    try:
        res = supabase.auth.refresh_session(body.refresh_token)
        if not res.session:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = auth_svc.get_user_by_supabase_uid(res.user.id)
    if not user:
        raise HTTPException(status_code=401, detail="Local identity missing")

    return ApiResponse(
        data=TokenResponse(
            access_token=res.session.access_token,
            refresh_token=res.session.refresh_token,
            user=UserPublic.model_validate(user, from_attributes=True),
        ),
        message="Token refreshed.",
    )


# logout
@router.post(
    "/logout",
    response_model=ApiResponse[None],
    summary="Logout user",
)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
):
    if credentials:
        try:
            get_supabase_anon().auth.sign_out()
        except Exception as e:
            logger.warning("Supabase logout failed: %s", e)
    return ApiResponse(data=None, message="Logged out successfully.")


# get current authenticated user
@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get current authenticated user",
)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return UserPublic.model_validate(current_user, from_attributes=True)


# create login user
@router.post(
    "/users",
    response_model=ApiResponse[UserPublic],
    summary="Create a new login user",
)
def create_login_user(
    body: CreateUserRequest,
    _user: User = Depends(require_admin),
    auth_svc: AuthService = Depends(get_auth_service),
):
    new_user = auth_svc.link_employee_to_new_user(
        employee_id=body.employee_id,
        username=body.username,
        raw_password=body.password,
        role=body.role,
    )
    return ApiResponse(
        data=UserPublic.model_validate(new_user, from_attributes=True),
        message="User account created.",
    )


# reset password
@router.post(
    "/users/{user_id}/reset-password",
    response_model=ApiResponse[None],
    summary="Force reset a user's password",
)
def reset_password(
    user_id: int,
    body: ResetPasswordRequest,
    _user: User = Depends(require_admin),
    auth_svc: AuthService = Depends(get_auth_service),
):
    auth_svc.force_reset_password(user_id=user_id, new_password=body.new_password)
    return ApiResponse(data=None, message="Password reset successfully.")


# change own password
@router.post(
    "/change-password",
    response_model=ApiResponse[None],
    summary="Change own password",
)
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    auth_svc: AuthService = Depends(get_auth_service),
):
    auth_svc.change_password(
        user=current_user,
        current_password=body.current_password,
        new_password=body.new_password,
    )
    return ApiResponse(data=None, message="Password changed successfully.")


# forgot password
@router.post(
    "/forgot-password",
    response_model=ApiResponse[None],
    summary="Request password reset email",
)
def forgot_password(
    body: ForgotPasswordRequest,
    auth_svc: AuthService = Depends(get_auth_service),
):
    auth_svc.forgot_password(email=body.email)
    return ApiResponse(
        data=None,
        message="If the email exists, a password reset link has been sent.",
    )


# update own profile
@router.patch(
    "/me",
    response_model=ApiResponse[UserPublic],
    summary="Update own profile",
)
def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    auth_svc: AuthService = Depends(get_auth_service),
):
    dto = UpdateProfileInput(username=body.username)
    updated = auth_svc.update_profile(user=current_user, dto=dto)
    if body.email:
        auth_svc.change_email(user=current_user, new_email=body.email)
    return ApiResponse(
        data=UserPublic.model_validate(updated, from_attributes=True),
        message="Profile updated.",
    )


@router.get(
    "/me/sessions",
    response_model=ApiResponse[list[UserSessionDTO]],
    summary="List active sessions",
)
def list_sessions(
    current_user: User = Depends(get_current_user),
    auth_svc: AuthService = Depends(get_auth_service),
):
    sessions = auth_svc.list_sessions(current_user)
    return ApiResponse(data=sessions)


@router.get(
    "/me/activity",
    response_model=ApiResponse[list],
    summary="List recent account activity",
)
def list_my_activity(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    audit_svc = Depends(get_audit_service),
):
    result = audit_svc.query_logs(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        data=[l.model_dump() for l in result.items],
    )


# logout all sessions
@router.post(
    "/me/sessions/logout-all",
    response_model=ApiResponse[None],
    summary="Revoke all sessions",
)
def logout_all_sessions(
    current_user: User = Depends(get_current_user),
    auth_svc: AuthService = Depends(get_auth_service),
):
    auth_svc.logout_all_sessions(current_user)
    return ApiResponse(data=None, message="All sessions revoked.")


# MFA status stub
@router.get(
    "/me/mfa/status",
    response_model=ApiResponse,
    summary="Get MFA enrollment status",
)
def mfa_status(
    current_user: User = Depends(get_current_user),
):
    return ApiResponse(data={"enrolled": False})


# MFA enroll stub
@router.post(
    "/me/mfa/enroll",
    response_model=ApiResponse[None],
    summary="Enroll in MFA (stub)",
)
def mfa_enroll(
    current_user: User = Depends(get_current_user),
):
    return ApiResponse(data=None, message="MFA enrollment is coming soon.")


# register with invite token
@router.post(
    "/register",
    response_model=ApiResponse[UserPublic],
    summary="Register with invite token",
)
def register(
    body: RegisterUserRequest,
    auth_svc: AuthService = Depends(get_auth_service),
):
    user = auth_svc.register_with_invite(
        token=body.token,
        username=body.username,
        password=body.password,
    )
    return ApiResponse(
        data=UserPublic.model_validate(user, from_attributes=True),
        message="Registration complete.",
    )
