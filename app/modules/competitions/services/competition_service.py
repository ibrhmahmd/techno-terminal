from datetime import date
from typing import Optional
from app.db.connection import get_session
import app.modules.competitions.repositories.competition_repository as comp_repo
import app.modules.competitions.repositories.team_repository as team_repo
from app.shared.exceptions import NotFoundError, BusinessRuleError
from app.modules.competitions.schemas.competition_schemas import (
    CreateCompetitionInput,
    CompetitionDTO,
    CategoryInfoDTO,
)
from app.modules.competitions.schemas.team_schemas import (
    CompetitionSummaryDTO,
    CategoryWithTeamsDTO,
    TeamWithMembersDTO,
    TeamDTO,
    TeamMemberDTO,
)


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
            db.commit()
            db.refresh(comp)
            return CompetitionDTO.model_validate(comp)

    def list_competitions(self) -> list[CompetitionDTO]:
        with get_session() as db:
            comps = comp_repo.list_competitions(db)
            return [CompetitionDTO.model_validate(c) for c in comps]

    def get_competition_by_id(self, competition_id: int) -> CompetitionDTO | None:
        """Get a single competition by ID."""
        with get_session() as db:
            comp = comp_repo.get_competition(db, competition_id)
            return CompetitionDTO.model_validate(comp) if comp else None

    def update_competition(self, competition_id: int, **kwargs) -> CompetitionDTO | None:
        with get_session() as db:
            comp = comp_repo.update_competition(db, competition_id, **kwargs)
            if comp:
                db.commit()
                db.refresh(comp)
            return CompetitionDTO.model_validate(comp) if comp else None

    def delete_competition(self, competition_id: int) -> bool:
        """Hard delete a competition."""
        with get_session() as db:
            teams = team_repo.list_teams(db, competition_id)
            if teams:
                raise BusinessRuleError(
                    "Cannot delete competition that has teams. Delete teams first."
                )
            result = comp_repo.delete_competition(db, competition_id)
            db.commit()
            return result

    def list_categories(self, competition_id: int) -> list[CategoryInfoDTO]:
        """
        List all distinct categories with their subcategories for a competition.
        Uses the teams table to derive categories (3-table design).
        """
        with get_session() as db:
            cat_rows = team_repo.get_distinct_categories(db, competition_id)

            cat_map = {}
            for row in cat_rows:
                if row.category not in cat_map:
                    cat_map[row.category] = set()
                if row.subcategory:
                    cat_map[row.category].add(row.subcategory)

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
        Uses batch loading: single JOIN query instead of N+1.
        """
        from app.modules.competitions.schemas.team_schemas import (
            TeamWithMembersDTO,
            CategoryWithTeamsDTO,
        )

        with get_session() as db:
            summary_data = comp_repo.get_competition_summary_data(db, competition_id)
            if not summary_data.competition:
                return None

            category_map: dict[tuple, list] = {}
            for team_dto in summary_data.teams:
                key = (team_dto.category, team_dto.subcategory)
                category_map.setdefault(key, []).append(team_dto)

            cat_dtos = []
            for (category, subcategory), team_list in category_map.items():
                team_dtos = []
                for team_dto in team_list:
                    member_rows = summary_data.members_by_team.get(team_dto.id, [])
                    team_dtos.append(
                        TeamWithMembersDTO(
                            team=team_dto,
                            members=[mwr.member for mwr in member_rows]
                        )
                    )

                cat_dtos.append(
                    CategoryWithTeamsDTO(
                        category=category,
                        subcategory=subcategory,
                        teams=team_dtos
                    )
                )

            return CompetitionSummaryDTO(
                competition=summary_data.competition,
                categories=cat_dtos
            )
