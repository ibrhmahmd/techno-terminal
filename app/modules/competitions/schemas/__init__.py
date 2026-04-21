from .competition_schemas import (
    CompetitionDTO,
    CreateCompetitionInput,
)

from .team_schemas import (
    TeamDTO,
    TeamMemberDTO,
    RegisterTeamInput,
    PayCompetitionFeeInput,
    StudentCompetitionDTO,
    TeamRegistrationResultDTO,
    AddTeamMemberResultDTO,
    TeamMemberRosterDTO,
    PayCompetitionFeeResponseDTO,
    CompetitionSummaryDTO,
    CategoryWithTeamsDTO,
    TeamWithMembersDTO,
)

__all__ = [
    # Basic DTOs
    "CompetitionDTO",
    "TeamDTO",
    "TeamMemberDTO",
    
    # Input Commands
    "CreateCompetitionInput",
    "RegisterTeamInput",
    "PayCompetitionFeeInput",
    
    # Aggregate Outputs
    "StudentCompetitionDTO",
    "TeamRegistrationResultDTO",
    "AddTeamMemberResultDTO",
    "TeamMemberRosterDTO",
    "PayCompetitionFeeResponseDTO",
    "CompetitionSummaryDTO",
    "CategoryWithTeamsDTO",
    "TeamWithMembersDTO",
]
