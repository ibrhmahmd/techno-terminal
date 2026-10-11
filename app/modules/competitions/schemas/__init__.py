from .competition_schemas import (
    CompetitionDTO,
    CreateCompetitionInput,
    CategoryInfoDTO,
)

from .team_schemas import (
    TeamDTO,
    TeamMemberDTO,
    RegisterTeamInput,
    AddTeamMemberInput,
    StudentCompetitionDTO,
    TeamRegistrationResultDTO,
    TeamRegistrationResultWithWarningDTO,
    AddTeamMemberResultDTO,
    AddTeamMemberResultWithWarningDTO,
    TeamMemberRosterDTO,
    CompetitionSummaryDTO,
    CompetitionSummaryDataDTO,
    CategoryWithTeamsDTO,
    TeamWithMembersDTO,
    CategorySubcategoryDTO,
    TeamMemberWithNameDTO,
    StudentMembershipEnrichedDTO,
)

__all__ = [
    # Basic DTOs
    "CompetitionDTO",
    "CategoryInfoDTO",
    "TeamDTO",
    "TeamMemberDTO",
    
    # Input Commands
    "CreateCompetitionInput",
    "RegisterTeamInput",
    "AddTeamMemberInput",
    
    # Aggregate Outputs
    "StudentCompetitionDTO",
    "TeamRegistrationResultDTO",
    "TeamRegistrationResultWithWarningDTO",
    "AddTeamMemberResultDTO",
    "AddTeamMemberResultWithWarningDTO",
    "TeamMemberRosterDTO",
    "CompetitionSummaryDTO",
    "CompetitionSummaryDataDTO",
    "CategoryWithTeamsDTO",
    "TeamWithMembersDTO",
    "CategorySubcategoryDTO",
    "TeamMemberWithNameDTO",
    "StudentMembershipEnrichedDTO",
]
