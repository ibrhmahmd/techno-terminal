"""
app/api/routers/academics/sessions.py
─────────────────────────────────────
Sessions router.

Endpoints for session management.
"""
from datetime import date
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.schemas.common import ApiResponse
from app.api.schemas.academics.session import SessionPublic, DailyScheduleItem
from app.api.dependencies import require_admin, require_any, get_session_service
from app.modules.academics.schemas import AddExtraSessionInput, UpdateSessionDTO
from app.modules.auth import User
from app.modules.academics.services.session_service import SessionService
from app.db.connection import get_session
from app.modules.academics.models import CourseSession

router = APIRouter(tags=["Academics — Sessions"])

# get daily schedule
@router.get(
    "/academics/sessions/daily-schedule",
    response_model=ApiResponse[list[DailyScheduleItem]],
    summary="Get daily session schedule",
)
def get_daily_schedule(
    target_date: date = Query(default_factory=date.today, description="Date to fetch schedule for"),
    _user: User = Depends(require_any),
    svc: SessionService = Depends(get_session_service),
):
    sessions = svc.get_daily_schedule(target_date)
    return ApiResponse(data=[DailyScheduleItem.model_validate(s) for s in sessions])


# add an extra session to a group
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
    session_data = body.model_copy(update={"group_id": group_id})
    session = svc.add_extra_session(session_data)
    return ApiResponse(
        data=SessionPublic.model_validate(session),
        message="Extra session added.",
    )


# get session details
@router.get(
    "/academics/sessions/{session_id}",
    response_model=ApiResponse[SessionPublic],
    summary="Get session details",
)
def get_session_endpoint(
    session_id: int,
    _user: User = Depends(require_any),
):
    with get_session() as db:
        cs = db.get(CourseSession, session_id)
        if not cs:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Session not found")
        return ApiResponse(data=SessionPublic.model_validate(cs))


# update a session
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


# delete a session
@router.delete(
    "/academics/sessions/{session_id}",
    response_model=ApiResponse[None],
    summary="Delete a session",
)
def delete_session(
    session_id: int,
    _user: User = Depends(require_admin),
    svc: SessionService = Depends(get_session_service),
):
    svc.delete_session(session_id)
    return ApiResponse(data=None, message="Session deleted successfully.")


# cancel a session
@router.post(
    "/academics/sessions/{session_id}/cancel",
    response_model=ApiResponse[SessionPublic],
    summary="Cancel a session",
)
def cancel_session(
    session_id: int,
    _user: User = Depends(require_admin),
    svc: SessionService = Depends(get_session_service),
):
    session = svc.cancel_session(session_id)
    return ApiResponse(
        data=SessionPublic.model_validate(session),
        message="Session cancelled and rescheduled successfully."
    )


# reactivate a cancelled session
@router.post(
    "/academics/sessions/{session_id}/reactivate",
    response_model=ApiResponse[SessionPublic],
    summary="Reactivate a cancelled session",
)
def reactivate_session(
    session_id: int,
    _user: User = Depends(require_admin),
    svc: SessionService = Depends(get_session_service),
):
    """
    Reactivate a previously cancelled session.
    Restores the session to scheduled status and removes the replacement session.
    """
    session = svc.reactivate_session(session_id)
    return ApiResponse(
        data=SessionPublic.model_validate(session),
        message="Session reactivated successfully."
    )


class SubstituteInstructorRequest(BaseModel):
    instructor_id: int

@router.post(
    "/academics/sessions/{session_id}/substitute",
    response_model=ApiResponse[SessionPublic],
    summary="Mark substitute instructor",
)
def substitute_instructor(
    session_id: int,
    body: SubstituteInstructorRequest,
    _user: User = Depends(require_admin),
    svc: SessionService = Depends(get_session_service),
):
    session = svc.mark_substitute_instructor(session_id, body.instructor_id)
    return ApiResponse(
        data=SessionPublic.model_validate(session),
        message="Substitute instructor marked successfully."
    )
