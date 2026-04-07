from app.db.connection import get_session
import app.modules.competitions.repositories.competition_repository as comp_repo
import app.modules.competitions.repositories.team_repository as team_repo
from app.shared.exceptions import NotFoundError
from app.modules.competitions.schemas.competition_schemas import (
    CreateCompetitionInput,
    AddCategoryInput,
    CompetitionDTO,
    CompetitionCategoryDTO,
)
from app.modules.competitions.schemas.team_schemas import (
    CompetitionSummaryDTO,
    CategoryWithTeamsDTO,
    TeamWithMembersDTO,
    TeamDTO,
    TeamMemberDTO,
)


class CompetitionService:
    """Service layer for managing Competitions and Categories."""

    def create_competition(self, cmd: CreateCompetitionInput) -> CompetitionDTO:
        with get_session() as db:
            comp = comp_repo.create_competition(
                db, 
                name=cmd.name, 
                edition=cmd.edition, 
                competition_date=cmd.competition_date, 
                location=cmd.location, 
                notes=cmd.notes
            )
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
            return CompetitionDTO.model_validate(comp) if comp else None


    def delete_competition(self, competition_id: int) -> bool:
        with get_session() as db:
            return comp_repo.delete_competition(db, competition_id)

    def add_category(self, cmd: AddCategoryInput) -> CompetitionCategoryDTO:
        with get_session() as db:
            comp = comp_repo.get_competition(db, cmd.competition_id)
            if not comp:
                raise NotFoundError(f"Competition {cmd.competition_id} not found.")
            cat = comp_repo.add_category(
                db, 
                competition_id=cmd.competition_id, 
                category_name=cmd.category_name, 
                notes=cmd.notes
            )
            return CompetitionCategoryDTO.model_validate(cat)

    def list_categories(self, competition_id: int) -> list[CompetitionCategoryDTO]:
        with get_session() as db:
            cats = comp_repo.list_categories(db, competition_id)
            return [CompetitionCategoryDTO.model_validate(c) for c in cats]

    def update_category(self, category_id: int, **kwargs) -> CompetitionCategoryDTO | None:
        with get_session() as db:
            cat = comp_repo.update_category(db, category_id, **kwargs)
            return CompetitionCategoryDTO.model_validate(cat) if cat else None

    def delete_category(self, category_id: int) -> bool:
        with get_session() as db:
            return comp_repo.delete_category(db, category_id)

    def get_competition_summary(self, competition_id: int) -> CompetitionSummaryDTO | None:
        """Returns competition + all categories + teams + member fee status."""
        with get_session() as db:
            comp = comp_repo.get_competition(db, competition_id)
            if not comp:
                return None
            
            categories = comp_repo.list_categories(db, competition_id)
            cat_dtos = []
            
            for cat in categories:
                teams = team_repo.list_teams(db, cat.id)
                team_dtos = []
                
                for team in teams:
                    members = team_repo.list_team_members(db, team.id)
                    team_dtos.append(
                        TeamWithMembersDTO(
                            team=TeamDTO.model_validate(team),
                            members=[TeamMemberDTO.model_validate(m) for m in members]
                        )
                    )
                    
                cat_dtos.append(
                    CategoryWithTeamsDTO(
                        category=CompetitionCategoryDTO.model_validate(cat),
                        teams=team_dtos
                    )
                )
                
            return CompetitionSummaryDTO(
                competition=CompetitionDTO.model_validate(comp),
                categories=cat_dtos
            )
