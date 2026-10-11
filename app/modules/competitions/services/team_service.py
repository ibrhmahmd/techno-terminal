from typing import Optional
from sqlmodel import select
from fastapi import HTTPException
from app.shared.exceptions import BusinessRuleError
from app.modules.competitions.schemas.team_schemas import TeamDTO, TeamMemberDTO, TeamWithMembersDTO
from app.modules.competitions.models.team_models import Team
from app.modules.competitions.services.team_base import TeamServiceBase


class TeamService(TeamServiceBase):
    """Team queries and CRUD."""

    def get_team_for_user(
        self, team_id: int, current_user
    ) -> TeamDTO | None:
        """Get a team, enforcing admin or coach access within the same session."""
        team = self._teams.get_team(team_id)
        if not team:
            return None
        if current_user.is_admin:
            return TeamDTO.model_validate(team)
        if current_user.employee_id and team.coach_id == current_user.employee_id:
            return TeamDTO.model_validate(team)
        raise HTTPException(status_code=403, detail="Access denied. Admin or team coach required.")

    def list_teams(
        self,
        competition_id: int,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
    ) -> list[TeamDTO]:
        """List teams for a competition with optional filters."""
        teams = self._teams.list_teams(competition_id, category, subcategory)
        return [TeamDTO.model_validate(t) for t in teams]

    def list_teams_for_coach(
        self,
        competition_id: int,
        coach_id: int,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
    ) -> list[TeamDTO]:
        """List teams for a competition filtered by coach_id."""
        db = self._uow.session
        stmt = select(Team).where(
            Team.competition_id == competition_id,
            Team.coach_id == coach_id,
        )
        if category:
            stmt = stmt.where(Team.category == category)
        if subcategory:
            stmt = stmt.where(Team.subcategory == subcategory)
        teams = list(db.exec(stmt).all())
        return [TeamDTO.model_validate(t) for t in teams]

    def list_teams_for_user(
        self,
        competition_id: int,
        current_user,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
    ) -> list[TeamDTO]:
        """List teams scoped to user role. Coaches see only their own teams."""
        if not current_user.is_admin and current_user.employee_id:
            return self.list_teams_for_coach(competition_id, current_user.employee_id, category, subcategory)
        return self.list_teams(competition_id, category, subcategory)

    def get_teams_with_members_for_user(
        self,
        competition_id: int,
        current_user,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
    ) -> list[TeamWithMembersDTO]:
        """List teams with members, scoped to user role."""
        teams = self.list_teams_for_user(competition_id, current_user, category, subcategory)
        result = []
        for team_dto in teams:
            members = self.get_team_members_for_team(team_dto.id)
            result.append(
                TeamWithMembersDTO(
                    team=team_dto,
                    members=members,
                )
            )
        return result

    def get_team_members_for_team(self, team_id: int) -> list[TeamMemberDTO]:
        """Get team members for a team."""
        members = self._teams.list_team_members(team_id)
        return [TeamMemberDTO.model_validate(m) for m in members]

    def update_team(self, team_id: int, **kwargs) -> TeamDTO | None:
        """Update team fields."""
        db = self._uow.session
        team = self._teams.update_team(team_id, **kwargs)
        if team:
            self._uow.commit()
            db.refresh(team)
        return TeamDTO.model_validate(team) if team else None

    def delete_team(self, team_id: int) -> bool:
        """Hard delete a team."""
        members = self._teams.list_team_members(team_id)
        for m in members:
            if m.amount_paid > 0:
                raise BusinessRuleError(
                    "Cannot delete team with members who have paid fees."
                )
        result = self._teams.delete_team(team_id)
        self._uow.commit()
        return result
