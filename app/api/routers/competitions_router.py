"""
app/api/routers/competitions.py
───────────────────────────────
Competitions domain router (Stub Phase 5).

Prefix: /api/v1 (mounted in main.py)
Tag:    Competitions
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.schemas.common import ApiResponse
from app.api.dependencies import require_any, require_admin, get_competition_service
from app.modules.auth import User
from app.modules.competitions import CompetitionService, CompetitionDTO

router = APIRouter(tags=["Competitions"])


class RegisterTeamInputStub(BaseModel):
    competition_category_id: int
    team_name: str
    member_student_ids: list[int]


# list all competitions
@router.get(
    "/competitions",
    response_model=ApiResponse[list[CompetitionDTO]],
    summary="List all competitions",
)
def list_competitions(
    _user: User = Depends(require_any),
    svc: CompetitionService = Depends(get_competition_service),
):
    """
    Returns a list of all competitions.
    """
    comps = svc.list_competitions()
    return ApiResponse(data=comps)


# register a team for a competition
@router.post(
    "/competitions/register",
    status_code=501,
    summary="Register a team for a competition (Not Implemented)",
)
def register_team(body: RegisterTeamInputStub, _user: User = Depends(require_admin)):
    """
    Placeholder endpoint for Team Registration.
    Write logic will be mapped in the post-launch sprint.
    """
    raise HTTPException(
        status_code=501,
        detail="Team registration endpoint not yet implemented. Use Streamlit UI for team registration."
    )
