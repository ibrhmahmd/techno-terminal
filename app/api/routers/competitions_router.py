"""
app/api/routers/competitions.py
───────────────────────────────
Competitions domain router (Stub Phase 5).

Prefix: /api/v1 (mounted in main.py)
Tag:    Competitions
"""

from typing import Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.schemas.common import ApiResponse
from app.api.dependencies import require_any, require_admin
from app.modules.auth import User
from app.modules.competitions import competition_service, CompetitionDTO

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
def list_competitions(_user: User = Depends(require_any)):
    """
    Returns a list of all competitions.
    """
    comps = competition_service.list_competitions()
    return ApiResponse(data=comps)


# register a team for a competition
@router.post(
    "/competitions/register",
    response_model=ApiResponse[Any],
    summary="Register a team for a competition (Stub)",
)
def register_team(body: RegisterTeamInputStub, _user: User = Depends(require_admin)):
    """
    Placeholder endpoint for Team Registration.
    Write logic will be mapped in the post-launch sprint.
    """
    return ApiResponse(
        data={"status": "queued", "team": body.team_name},
        message="Team registration stub.",
    )
