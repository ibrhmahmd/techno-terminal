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
    PayCompetitionFeeInput,
    StudentCompetitionDTO,
    TeamRegistrationResultDTO,
    TeamRegistrationResultWithWarningDTO,
    AddTeamMemberResultDTO,
    AddTeamMemberResultWithWarningDTO,
    TeamMemberRosterDTO,
    PayCompetitionFeeResponseDTO,
    CompetitionSummaryDTO,
    CompetitionSummaryDataDTO,
    CategoryWithTeamsDTO,
    TeamWithMembersDTO,
    CategorySubcategoryDTO,
    TeamMemberWithNameDTO,
    StudentMembershipEnrichedDTO,
    RefundCompetitionFeeBody,
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
    "PayCompetitionFeeInput",
    "RefundCompetitionFeeBody",
    
    # Aggregate Outputs
    "StudentCompetitionDTO",
    "TeamRegistrationResultDTO",
    "TeamRegistrationResultWithWarningDTO",
    "AddTeamMemberResultDTO",
    "AddTeamMemberResultWithWarningDTO",
    "TeamMemberRosterDTO",
    "PayCompetitionFeeResponseDTO",
    "CompetitionSummaryDTO",
    "CompetitionSummaryDataDTO",
    "CategoryWithTeamsDTO",
    "TeamWithMembersDTO",
    "CategorySubcategoryDTO",
    "TeamMemberWithNameDTO",
    "StudentMembershipEnrichedDTO",
]
