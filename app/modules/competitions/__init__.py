"""
app/modules/competitions/__init__.py
───────────────────────────────────
Domain-Driven facade for the Competitions module.
Re-exports Models, Schemas, and the new Service layer singletons.
"""

# ── 1. Scoped Models Re-exports
from .models.competition_models import Competition, CompetitionCategory
from .models.team_models import Team, TeamMember

# ── 2. Unified Schema Re-exports
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

# ── 3. Service Instantiation & Re-exports
from .services.competition_service import CompetitionService
from .services.team_service import TeamService

_competition_svc = CompetitionService()
_team_svc = TeamService()

# Map legacy function signatures logically into the new singleton methods
get_student_competitions = _team_svc.get_student_competitions
create_competition = _competition_svc.create_competition
list_competitions = _competition_svc.list_competitions
update_competition = _competition_svc.update_competition
delete_competition = _competition_svc.delete_competition
add_category = _competition_svc.add_category
list_categories = _competition_svc.list_categories
update_category = _competition_svc.update_category
delete_category = _competition_svc.delete_category
register_team = _team_svc.register_team
list_teams = _team_svc.list_teams
update_team = _team_svc.update_team
delete_team = _team_svc.delete_team
add_team_member_to_existing = _team_svc.add_team_member_to_existing
remove_team_member = _team_svc.remove_team_member
list_team_members = _team_svc.list_team_members
pay_competition_fee = _team_svc.pay_competition_fee
get_competition_summary = _competition_svc.get_competition_summary
unmark_team_fee_for_payment = _team_svc.unmark_team_fee_for_payment

__all__ = [
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
    
    # Services
    "get_student_competitions",
    "create_competition",
    "list_competitions",
    "update_competition",
    "delete_competition",
    "add_category",
    "list_categories",
    "update_category",
    "delete_category",
    "register_team",
    "list_teams",
    "update_team",
    "delete_team",
    "add_team_member_to_existing",
    "remove_team_member",
    "list_team_members",
    "pay_competition_fee",
    "get_competition_summary",
    "unmark_team_fee_for_payment",
]
