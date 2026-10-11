"""
app/modules/competitions/__init__.py
────────────────────────────────────
Competitions Module Facade (ADR-0003)

Other modules must import Competitions ONLY via this facade, except
app.modules.competitions.models which anyone may import (ADR-0004).
"""

from .services.competition_service import CompetitionService
from .services.team_service import TeamService
from .services.team_fee_service import TeamFeeService

from .models.competition_models import Competition
from .models.team_models import Team, TeamMember

from .schemas import (
    # Basic DTOs
    CompetitionDTO,
    TeamDTO,
    TeamMemberDTO,
    # Input Commands
    CreateCompetitionInput,
    RegisterTeamInput,
    AddTeamMemberInput,
    # Outputs
    StudentCompetitionDTO,
    TeamRegistrationResultDTO,
    AddTeamMemberResultDTO,
    TeamMemberRosterDTO,
    CompetitionSummaryDTO,
    CategoryWithTeamsDTO,
    TeamWithMembersDTO,
)

__all__ = [
    # Service Classes
    "CompetitionService",
    "TeamService",
    "TeamFeeService",
    # Models
    "Competition",
    "Team",
    "TeamMember",
    # Schemas
    "CompetitionDTO",
    "TeamDTO",
    "TeamMemberDTO",
    "CreateCompetitionInput",
    "RegisterTeamInput",
    "AddTeamMemberInput",
    "StudentCompetitionDTO",
    "TeamRegistrationResultDTO",
    "AddTeamMemberResultDTO",
    "TeamMemberRosterDTO",
    "CompetitionSummaryDTO",
    "CategoryWithTeamsDTO",
    "TeamWithMembersDTO",
]
