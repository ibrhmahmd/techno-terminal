"""
app/api/routers/competitions/competitions_router.py
──────────────────────────────────────────────────
Competitions domain router for 3-table schema.

Handles: Competition lifecycle (CRUD, restore, categories, summary)
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.schemas.common import ApiResponse
from app.api.dependencies import require_any, require_admin, get_competition_service
from app.modules.auth import User
from app.modules.competitions import CompetitionService, CompetitionDTO

from app.modules.competitions.schemas.competition_schemas import (
    CreateCompetitionInput,
)

router = APIRouter(tags=["Competitions"])


# ── Helper DTOs ───────────────────────────────────────────────────────────────

class CategoryResponse(BaseModel):
    """Category info for API response (3-table schema)."""
    category: str
    subcategories: list[str]


class UpdateCompetitionInput(BaseModel):
    """Input for updating a competition (partial updates supported)."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    edition: Optional[str] = Field(None, max_length=100)
    edition_year: Optional[int] = Field(None, ge=2000, le=2100)
    competition_date: Optional[date] = None
    location: Optional[str] = Field(None, max_length=200)
    fee_per_student: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    notes: Optional[str] = Field(None, max_length=1000)


class CompetitionSummaryResponse(BaseModel):
    """Full competition summary with nested data."""
    competition: CompetitionDTO
    categories: list[dict]  # CategoryWithTeamsDTO serialized
    total_teams: int
    total_participants: int


# ── Competition Endpoints ─────────────────────────────────────────────────────

@router.get(
    "/competitions",
    response_model=ApiResponse[list[CompetitionDTO]],
    summary="List all competitions",
    description="Returns all active competitions. Use /competitions/deleted for soft-deleted items.",
)
def list_competitions(
    include_deleted: bool = Query(False, description="Include soft-deleted competitions (admin only)"),
    current_user: User = Depends(require_any),
    svc: CompetitionService = Depends(get_competition_service),
):
    """List all competitions."""
    # Only admins can see deleted competitions
    if include_deleted and current_user.is_admin:
        comps = svc.list_competitions(include_deleted=True)
    else:
        comps = svc.list_competitions()
    return ApiResponse(data=comps)


@router.post(
    "/competitions",
    response_model=ApiResponse[CompetitionDTO],
    status_code=201,
    summary="Create a new competition",
    description="Create a new competition with name, date, location, and fee settings.",
)
def create_competition(
    body: CreateCompetitionInput,
    current_user: User = Depends(require_admin),
    svc: CompetitionService = Depends(get_competition_service),
):
    """Create a new competition."""
    comp = svc.create_competition(body)
    return ApiResponse(
        data=CompetitionDTO.model_validate(comp),
        message="Competition created successfully."
    )


@router.get(
    "/competitions/{competition_id}",
    response_model=ApiResponse[CompetitionDTO],
    summary="Get competition details",
    description="Retrieve full details for a specific competition by ID.",
    responses={
        404: {"description": "Competition not found"},
    },
)
def get_competition(
    competition_id: int,
    current_user: User = Depends(require_any),
    svc: CompetitionService = Depends(get_competition_service),
):
    """Get single competition by ID."""
    comp = svc.get_competition_by_id(competition_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    return ApiResponse(data=CompetitionDTO.model_validate(comp))


@router.put(
    "/competitions/{competition_id}",
    response_model=ApiResponse[CompetitionDTO],
    summary="Update competition (full)",
    description="Full update of competition. All fields must be provided.",
    responses={
        404: {"description": "Competition not found"},
    },
)
def update_competition_full(
    competition_id: int,
    body: UpdateCompetitionInput,
    current_user: User = Depends(require_admin),
    svc: CompetitionService = Depends(get_competition_service),
):
    """Full update of competition."""
    # Check exists first
    existing = svc.get_competition_by_id(competition_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    # Filter out None values for update
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    
    comp = svc.update_competition(competition_id, **update_data)
    return ApiResponse(
        data=CompetitionDTO.model_validate(comp),
        message="Competition updated successfully."
    )


@router.patch(
    "/competitions/{competition_id}",
    response_model=ApiResponse[CompetitionDTO],
    summary="Update competition (partial)",
    description="Partial update of competition. Only provided fields are updated.",
    responses={
        404: {"description": "Competition not found"},
    },
)
def update_competition_partial(
    competition_id: int,
    body: UpdateCompetitionInput,
    current_user: User = Depends(require_admin),
    svc: CompetitionService = Depends(get_competition_service),
):
    """Partial update of competition."""
    # Same implementation as PUT - both support partial updates
    return update_competition_full(competition_id, body, current_user, svc)


@router.delete(
    "/competitions/{competition_id}",
    response_model=ApiResponse[bool],
    summary="Soft delete competition",
    description="Soft delete a competition. Cannot delete if teams are registered.",
    responses={
        404: {"description": "Competition not found"},
        409: {"description": "Cannot delete: competition has teams"},
    },
)
def delete_competition(
    competition_id: int,
    current_user: User = Depends(require_admin),
    svc: CompetitionService = Depends(get_competition_service),
):
    """Soft delete a competition."""
    result = svc.delete_competition(competition_id, deleted_by=current_user.id)
    return ApiResponse(data=result, message="Competition deleted successfully.")


@router.post(
    "/competitions/{competition_id}/restore",
    response_model=ApiResponse[bool],
    summary="Restore competition",
    description="Restore a soft-deleted competition.",
    responses={
        404: {"description": "Competition not found"},
    },
)
def restore_competition(
    competition_id: int,
    current_user: User = Depends(require_admin),
    svc: CompetitionService = Depends(get_competition_service),
):
    """Restore a soft-deleted competition."""
    result = svc.restore_competition(competition_id)
    return ApiResponse(data=result, message="Competition restored successfully.")


@router.get(
    "/competitions/deleted",
    response_model=ApiResponse[list[CompetitionDTO]],
    summary="List deleted competitions",
    description="List all soft-deleted competitions (admin only).",
)
def list_deleted_competitions(
    current_user: User = Depends(require_admin),
    svc: CompetitionService = Depends(get_competition_service),
):
    """List all soft-deleted competitions."""
    result = svc.list_deleted_competitions()
    return ApiResponse(data=result)


@router.get(
    "/competitions/{competition_id}/summary",
    response_model=ApiResponse[CompetitionSummaryResponse],
    summary="Get competition summary",
    description="Full competition dashboard with teams, categories, and statistics.",
    responses={
        404: {"description": "Competition not found"},
    },
)
def get_competition_summary(
    competition_id: int,
    current_user: User = Depends(require_any),
    svc: CompetitionService = Depends(get_competition_service),
):
    """Get full competition summary with all nested data."""
    summary = svc.get_competition_summary(competition_id)
    
    # Calculate totals
    total_teams = sum(len(cat.teams) for cat in summary.categories)
    total_participants = sum(
        len(team.members) if team.members else 0
        for cat in summary.categories
        for team in cat.teams
    )
    
    return ApiResponse(data=CompetitionSummaryResponse(
        competition=summary.competition,
        categories=[cat.model_dump() for cat in summary.categories],
        total_teams=total_teams,
        total_participants=total_participants,
    ))


@router.get(
    "/competitions/{competition_id}/categories",
    response_model=ApiResponse[list[CategoryResponse]],
    summary="List competition categories",
    description="List all distinct categories and subcategories for a competition.",
    responses={
        404: {"description": "Competition not found"},
    },
)
def list_categories(
    competition_id: int,
    current_user: User = Depends(require_any),
    svc: CompetitionService = Depends(get_competition_service),
):
    """List categories and subcategories for a competition."""
    cats = svc.list_categories(competition_id)
    return ApiResponse(data=[
        CategoryResponse(category=c.category, subcategories=c.subcategories)
        for c in cats
    ])
