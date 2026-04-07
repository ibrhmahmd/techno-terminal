"""
app/modules/competitions/__init__.py
───────────────────────────────────
Public API Facade for the Competitions module.
Exposes both service classes and shared schema types.
UI components import the two singletons below.
"""

from .services.competition_service import CompetitionService
from .services.team_service import TeamService

from .models.competition_models import Competition, CompetitionCategory
from .models.team_models import Team, TeamMember

from .schemas import (
    # Basic DTOs
    CompetitionDTO,
    CompetitionCategoryDTO,
    TeamDTO,
    TeamMemberDTO,
    # Input Commands
    CreateCompetitionInput,
    AddCategoryInput,
    RegisterTeamInput,
    PayCompetitionFeeInput,
    # Outputs
    StudentCompetitionDTO,
    TeamRegistrationResultDTO,
    AddTeamMemberResultDTO,
    TeamMemberRosterDTO,
    PayCompetitionFeeResponseDTO,
    CompetitionSummaryDTO,
    CategoryWithTeamsDTO,
    TeamWithMembersDTO,
)

# ── UI Singletons (one per service class — correct, no patch) ─────────────────
competition_service = CompetitionService()
team_service        = TeamService()

__all__ = [
    # Service Classes
    "CompetitionService",
    "TeamService",
    # UI Singletons
    "competition_service",
    "team_service",
    # Models
    "Competition",
    "CompetitionCategory",
    "Team",
    "TeamMember",
    # Schemas
    "CompetitionDTO",
    "CompetitionCategoryDTO",
    "TeamDTO",
    "TeamMemberDTO",
    "CreateCompetitionInput",
    "AddCategoryInput",
    "RegisterTeamInput",
    "PayCompetitionFeeInput",
    "StudentCompetitionDTO",
    "TeamRegistrationResultDTO",
    "AddTeamMemberResultDTO",
    "TeamMemberRosterDTO",
    "PayCompetitionFeeResponseDTO",
    "CompetitionSummaryDTO",
    "CategoryWithTeamsDTO",
    "TeamWithMembersDTO",
]
