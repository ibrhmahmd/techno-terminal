"""
app/modules/academics/services/group_competition_service.py
──────────────────────────────────────────────────────────
Service class for Group Competition integration.
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from app.shared.datetime_utils import utc_now

if TYPE_CHECKING:
    from app.modules.crm.services.activity_service import StudentActivityService

from app.db.connection import get_session
from app.modules.academics.models.group_level_models import GroupCompetitionParticipation
import app.modules.academics.group.competition.repository as repo
from app.modules.academics.group.competition.schemas import TeamReadDTO, GroupCompetitionDTO, WithdrawalResultDTO, TeamLinkResultDTO
from app.shared.exceptions import NotFoundError, ConflictError, BusinessRuleError


class GroupCompetitionService:
    """Service for managing group participation in competitions."""

    def __init__(self, activity_svc: Optional["StudentActivityService"] = None) -> None:
        self._activity_svc = activity_svc

    def get_teams_by_group(
        self,
        group_id: int,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[TeamReadDTO], int]:
        """
        Get paginated list of teams for a group.
        
        Args:
            group_id: The group ID to filter by
            include_inactive: Whether to include deleted teams
            skip: Number of records to skip (pagination)
            limit: Maximum records to return (pagination)
            
        Returns:
            Tuple of (list of TeamReadDTO, total count)
        """
        with get_session() as session:
            teams, total = repo.get_teams_by_group(
                session, group_id, include_inactive, skip, limit
            )
            return [TeamReadDTO.model_validate(t) for t in teams], total

    def register_team(
        self,
        group_id: int,
        team_id: int,
        competition_id: int,
        notes: str | None = None,
    ) -> GroupCompetitionParticipation:
        """
        Register a team for a competition on behalf of a group.
        
        Args:
            group_id: The group participating
            team_id: The team representing the group
            competition_id: Competition to register for
            category_id: Optional competition category
            notes: Optional notes
        
        Returns:
            Created participation record
        """
        with get_session() as session:
            # Check for existing active participation
            existing = repo.get_active_participation_for_team(
                session, group_id, team_id, competition_id
            )
            if existing:
                raise ConflictError(
                    f"Team {team_id} already has active participation in competition {competition_id}"
                )
            
            participation = GroupCompetitionParticipation(
                group_id=group_id,
                team_id=team_id,
                competition_id=competition_id,
                entered_at=utc_now(),
                is_active=True,
                notes=notes,
            )
            from app.shared.audit_utils import apply_create_audit
            apply_create_audit(participation)
            
            created = repo.create_participation(session, participation)
            session.commit()
            session.refresh(created)

            # Log competition registration for each team member
            if self._activity_svc:
                from app.modules.crm.interfaces.dtos.log_competition_registration_dto import LogCompetitionRegistrationDTO
                from app.modules.competitions.models.team_models import TeamMember
                from sqlalchemy import select

                # Get team members
                stmt = select(TeamMember).where(TeamMember.team_id == team_id)
                members = session.exec(stmt).all()

                # Get competition name
                from app.modules.competitions.models.competition_models import Competition
                competition = session.get(Competition, competition_id)
                competition_name = competition.name if competition else "Unknown"

                for member in members:
                    if member.student_id:
                        self._activity_svc.log_competition_registration(
                            LogCompetitionRegistrationDTO(
                                student_id=member.student_id,
                                competition_id=competition_id,
                                competition_name=competition_name,
                                performed_by=None,  # TODO: Pass from caller
                            )
                        )

            return created

    def get_group_competitions(
        self, group_id: int, is_active: bool | None = True
    ) -> list[GroupCompetitionDTO]:
        """
        Get all competition participations for a group.
        
        Args:
            group_id: Group to query
            is_active: Filter by active status (None for all)
        
        Returns:
            List of participation records with enriched data
        """
        with get_session() as session:
            participations = repo.list_group_participations(session, group_id, is_active)
            result = []
            for p in participations:
                from app.modules.competitions.models.competition_models import Competition
                from app.modules.competitions.models.team_models import Team
                
                competition = session.get(Competition, p.competition_id)
                team = session.get(Team, p.team_id)

                result.append(GroupCompetitionDTO(
                    participation_id=p.id,
                    competition_id=p.competition_id,
                    competition_name=competition.name if competition else None,
                    category=team.category if team else None,
                    subcategory=team.subcategory if team else None,
                    team_id=p.team_id,
                    team_name=team.team_name if team else None,
                    entered_at=p.entered_at,
                    left_at=p.left_at,
                    is_active=p.is_active,
                    final_placement=p.final_placement,
                    notes=p.notes,
                ))
            return result

    def complete_participation(
        self,
        participation_id: int,
        final_placement: int | None = None,
    ) -> GroupCompetitionParticipation:
        """
        Mark a competition participation as completed.
        
        Args:
            participation_id: Participation record to complete
            final_placement: Optional final ranking/placement
        
        Returns:
            Updated participation record
        """
        with get_session() as session:
            participation = repo.complete_participation(
                session, participation_id, final_placement
            )
            if not participation:
                raise NotFoundError(f"Participation {participation_id} not found")
            session.commit()
            session.refresh(participation)
            return participation

    def update_participation_notes(
        self, participation_id: int, notes: str
    ) -> GroupCompetitionParticipation:
        """Update notes for a participation record."""
        with get_session() as session:
            participation = repo.get_participation_by_id(session, participation_id)
            if not participation:
                raise NotFoundError(f"Participation {participation_id} not found")
            
            participation.notes = notes
            participation.updated_at = utc_now()
            
            updated = repo.update_participation(session, participation)
            session.commit()
            session.refresh(updated)
            return updated

    def withdraw_from_competition(
        self, participation_id: int, reason: str | None = None
    ) -> WithdrawalResultDTO:
        """
        Withdraw from a competition.
        
        Args:
            participation_id: ID of the participation record
            reason: Optional reason for withdrawal
            
        Returns:
            Withdrawal result DTO
            
        Raises:
            ValueError: If participation not found or cannot be withdrawn
        """
        from datetime import datetime
        
        with get_session() as session:
            participation = repo.get_participation_by_id(session, participation_id)
            if not participation:
                raise NotFoundError(f"Participation {participation_id} not found")
            
            # Check if already completed or withdrawn
            if participation.is_active == False:
                raise BusinessRuleError("Already withdrawn or completed")
            
            # Mark as inactive (withdrawn)
            participation.is_active = False
            participation.left_at = utc_now()
            participation.notes = reason or participation.notes
            
            updated = repo.update_participation(session, participation)
            session.commit()
            
            return WithdrawalResultDTO(
                id=updated.id,
                status="withdrawn",
                withdrawn_at=updated.left_at,
            )

    def link_existing_team(self, group_id: int, team_id: int) -> TeamLinkResultDTO:
        """
        Link an existing team to a group (if not already linked).
        
        Args:
            group_id: Group to link team to
            team_id: Team to link
        
        Returns:
            Updated team data
        """
        with get_session() as session:
            from app.modules.competitions.models.team_models import Team
            
            team = session.get(Team, team_id)
            if not team:
                raise NotFoundError(f"Team {team_id} not found")
            
            # Update team's group_id
            team.group_id = group_id
            session.add(team)
            session.commit()
            session.refresh(team)
            
            return TeamLinkResultDTO(
                team_id=team.id,
                team_name=team.team_name,
                group_id=team.group_id,
            )
