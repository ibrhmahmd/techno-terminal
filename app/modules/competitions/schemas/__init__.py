from .competition_schemas import (
    CompetitionDTO,
    CompetitionCategoryDTO,
    CreateCompetitionInput,
    AddCategoryInput,
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
    "CompetitionCategoryDTO",
    "TeamDTO",
    "TeamMemberDTO",
    
    # Input Commands
    "CreateCompetitionInput",
    "AddCategoryInput",
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
