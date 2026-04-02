"""
app/api/routers/academics/sessions.py
─────────────────────────────────────
Sessions router.

Endpoints for session management.
"""
from fastapi import APIRouter, Depends

from app.api.schemas.common import ApiResponse
from app.api.schemas.academics.session import SessionPublic
from app.api.dependencies import require_admin, get_session_service
from app.modules.academics.schemas import AddExtraSessionInput, UpdateSessionDTO
from app.modules.auth import User
from app.modules.academics.services.session_service import SessionService

router = APIRouter(tags=["Academics — Sessions"])


@router.post(
    "/academics/groups/{group_id}/sessions",
    response_model=ApiResponse[SessionPublic],
    status_code=201,
    summary="Add an extra session to a group",
)
def add_extra_session(
    group_id: int,
    body: AddExtraSessionInput,
    _user: User = Depends(require_admin),
    svc: SessionService = Depends(get_session_service),
):
    # URL path is source of truth for group_id
    session_data = body.model_copy(update={"group_id": group_id})
    session = svc.add_extra_session(session_data)
    return ApiResponse(
        data=SessionPublic.model_validate(session),
        message="Extra session added.",
    )


@router.patch(
    "/academics/sessions/{session_id}",
    response_model=ApiResponse[SessionPublic],
    summary="Update a session (date, time, status, notes)",
)
def update_session(
    session_id: int,
    body: UpdateSessionDTO,
    _user: User = Depends(require_admin),
    svc: SessionService = Depends(get_session_service),
):
    session = svc.update_session(session_id, body)
    return ApiResponse(data=SessionPublic.model_validate(session))
