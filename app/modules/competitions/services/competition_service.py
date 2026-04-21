from datetime import date
from typing import Optional
from app.db.connection import get_session
import app.modules.competitions.repositories.competition_repository as comp_repo
import app.modules.competitions.repositories.team_repository as team_repo
from app.shared.exceptions import NotFoundError, BusinessRuleError
from app.modules.competitions.schemas.competition_schemas import (
    CreateCompetitionInput,
    CompetitionDTO,
)
from app.modules.competitions.schemas.team_schemas import (
    CompetitionSummaryDTO,
    CategoryWithTeamsDTO,
    TeamWithMembersDTO,
    TeamDTO,
    TeamMemberDTO,
    TeamMemberRosterDTO,
)


class CategoryInfoDTO:
    """Simple DTO for category/subcategory info."""
    def __init__(self, category: str, subcategories: list[str]):
        self.category = category
        self.subcategories = subcategories


class CompetitionService:
    """Service layer for managing Competitions with 3-table schema."""

    def create_competition(self, cmd: CreateCompetitionInput) -> CompetitionDTO:
        with get_session() as db:
            comp = comp_repo.create_competition(
                db,
                name=cmd.name,
                edition=cmd.edition,
                competition_date=cmd.competition_date,
                location=cmd.location,
                notes=cmd.notes,
                fee_per_student=cmd.fee_per_student,
                edition_year=cmd.competition_date.year if cmd.competition_date else None
            )
            return CompetitionDTO.model_validate(comp)

    def list_competitions(self, include_deleted: bool = False) -> list[CompetitionDTO]:
        with get_session() as db:
            comps = comp_repo.list_competitions(db, include_deleted=include_deleted)
            return [CompetitionDTO.model_validate(c) for c in comps]

    def get_competition_by_id(self, competition_id: int) -> CompetitionDTO | None:
        """Get a single competition by ID."""
        with get_session() as db:
            comp = comp_repo.get_competition(db, competition_id)
            return CompetitionDTO.model_validate(comp) if comp else None

    def update_competition(self, competition_id: int, **kwargs) -> CompetitionDTO | None:
        with get_session() as db:
            comp = comp_repo.update_competition(db, competition_id, **kwargs)
            return CompetitionDTO.model_validate(comp) if comp else None

    def delete_competition(self, competition_id: int, deleted_by: Optional[int] = None) -> bool:
        """Soft delete a competition."""
        with get_session() as db:
            # Check if competition has teams
            teams = team_repo.list_teams(db, competition_id)
            if teams:
                raise BusinessRuleError(
                    "Cannot delete competition that has teams. Delete teams first."
                )
            return comp_repo.delete_competition(db, competition_id, deleted_by=deleted_by)

    def restore_competition(self, competition_id: int) -> bool:
        """Restore a soft-deleted competition."""
        with get_session() as db:
            return comp_repo.restore_competition(db, competition_id)

    def list_deleted_competitions(self) -> list[CompetitionDTO]:
        """List all soft-deleted competitions."""
        with get_session() as db:
            comps = comp_repo.list_deleted_competitions(db)
            return [CompetitionDTO.model_validate(c) for c in comps]

    def list_categories(self, competition_id: int) -> list[CategoryInfoDTO]:
        """
        List all distinct categories with their subcategories for a competition.
        Uses the teams table to derive categories (3-table design).
        """
        with get_session() as db:
            # Get distinct category/subcategory tuples from teams
            cat_tuples = team_repo.get_distinct_categories(db, competition_id)

            # Group by category
            cat_map = {}
            for category, subcategory in cat_tuples:
                if category not in cat_map:
                    cat_map[category] = set()
                if subcategory:
                    cat_map[category].add(subcategory)

            # Convert to DTOs
            return [
                CategoryInfoDTO(
                    category=cat,
                    subcategories=list(subs)
                )
                for cat, subs in cat_map.items()
            ]

    def get_competition_summary(self, competition_id: int) -> CompetitionSummaryDTO | None:
        """
        Returns competition + all categories + teams + member fee status.
        Uses 3-table schema: categories are derived from teams.
        """
        with get_session() as db:
            comp = comp_repo.get_competition(db, competition_id)
            if not comp:
                return None

            # Get all teams for this competition
            teams = team_repo.list_teams(db, competition_id)

            # Group teams by category/subcategory
            category_map = {}
            for team in teams:
                key = (team.category, team.subcategory)
                if key not in category_map:
                    category_map[key] = []
                category_map[key].append(team)

            # Build category DTOs
            cat_dtos = []
            for (category, subcategory), team_list in category_map.items():
                team_dtos = []
                for team in team_list:
                    members = team_repo.list_team_members(db, team.id)
                    # Enrich members with student names
                    member_dtos = []
                    for m in members:
                        # Get student name
                        from app.modules.crm.models.student_models import Student
                        student = db.get(Student, m.student_id)
                        member_dtos.append(
                            TeamMemberRosterDTO(
                                team_member_id=m.id,
                                student_id=m.student_id,
                                student_name=student.full_name if student else f"Student #{m.student_id}",
                                member_share=m.member_share,
                                fee_paid=m.fee_paid,
                                payment_id=m.payment_id,
                            )
                        )

                    team_dtos.append(
                        TeamWithMembersDTO(
                            team=TeamDTO.model_validate(team),
                            members=[TeamMemberDTO.model_validate(m) for m in members]
                        )
                    )

                # Create category DTO using 3-table schema (category as string)
                cat_dtos.append(
                    CategoryWithTeamsDTO(
                        category=category,
                        subcategory=subcategory,
                        teams=team_dtos
                    )
                )

            return CompetitionSummaryDTO(
                competition=CompetitionDTO.model_validate(comp),
                categories=cat_dtos
            )
