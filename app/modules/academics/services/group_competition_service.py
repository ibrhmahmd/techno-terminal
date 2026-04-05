"""
app/modules/academics/services/group_competition_service.py
──────────────────────────────────────────────────────────
Service class for Group Competition integration.
"""
from datetime import datetime

from app.db.connection import get_session
from app.modules.academics.models.group_level_models import GroupCompetitionParticipation
from app.modules.academics import repositories as repo


class GroupCompetitionService:
    """Service for managing group participation in competitions."""

    def register_team(
        self,
        group_id: int,
        team_id: int,
        competition_id: int,
        category_id: int | None = None,
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
                raise ValueError(
                    f"Team {team_id} already has active participation in competition {competition_id}"
                )
            
            participation = GroupCompetitionParticipation(
                group_id=group_id,
                team_id=team_id,
                competition_id=competition_id,
                category_id=category_id,
                entered_at=datetime.utcnow(),
                is_active=True,
                notes=notes,
            )
            
            created = repo.create_participation(session, participation)
            session.commit()
            session.refresh(created)
            return created

    def get_group_competitions(
        self, group_id: int, is_active: bool | None = True
    ) -> list[dict]:
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
                category = None
                if p.category_id:
                    from app.modules.competitions.models.competition_models import CompetitionCategory
                    category = session.get(CompetitionCategory, p.category_id)
                
                result.append({
                    "participation_id": p.id,
                    "competition_id": p.competition_id,
                    "competition_name": competition.name if competition else None,
                    "category_id": p.category_id,
                    "category_name": category.name if category else None,
                    "team_id": p.team_id,
                    "team_name": team.team_name if team else None,
                    "entered_at": p.entered_at,
                    "left_at": p.left_at,
                    "is_active": p.is_active,
                    "final_placement": p.final_placement,
                    "notes": p.notes,
                })
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
                raise ValueError(f"Participation {participation_id} not found")
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
                raise ValueError(f"Participation {participation_id} not found")
            
            participation.notes = notes
            participation.updated_at = datetime.utcnow()
            
            updated = repo.update_participation(session, participation)
            session.commit()
            session.refresh(updated)
            return updated

    def link_existing_team(self, group_id: int, team_id: int) -> dict:
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
                raise ValueError(f"Team {team_id} not found")
            
            # Update team's group_id
            team.group_id = group_id
            session.add(team)
            session.commit()
            session.refresh(team)
            
            return {
                "team_id": team.id,
                "team_name": team.team_name,
                "group_id": team.group_id,
            }
