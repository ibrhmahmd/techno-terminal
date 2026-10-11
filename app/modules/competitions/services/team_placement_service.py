from datetime import date
from typing import Optional
from app.db.uow import UnitOfWork
from app.shared.exceptions import NotFoundError, BusinessRuleError
from app.modules.competitions.schemas.team_schemas import TeamDTO
from app.modules.crm import StudentActivityService
from app.modules.competitions.services.team_base import TeamServiceBase

import logging
logger = logging.getLogger(__name__)


class TeamPlacementService(TeamServiceBase):
    """Team placement use case."""

    def update_placement(
        self,
        team_id: int,
        placement_rank: int,
        placement_label: Optional[str] = None,
        current_user_id: Optional[int] = None,
    ) -> TeamDTO:
        """
        Update team placement after competition.
        Can only be set after competition date has passed.
        """
        db = self._uow.session
        team = self._teams.get_team(team_id)
        if not team:
            raise NotFoundError(f"Team {team_id} not found.")

        comp = self._comps.get_competition(team.competition_id)
        if comp and comp.competition_date:
            if comp.competition_date > date.today():
                raise BusinessRuleError(
                    "Cannot set placement before competition date."
                )
            if (date.today() - comp.competition_date).days > 30:
                raise BusinessRuleError(
                    "Placement recording window closed. Placements must be "
                    "recorded within 30 days of the competition date."
                )

        team = self._teams.update_team(team_id,
            placement_rank=placement_rank,
            placement_label=placement_label
        )

        # Log activity for each team member
        if team:
            members = self._teams.list_team_members(team_id)
            for m in members:
                self._log_placement_activity(
                    db=db,
                    student_id=m.student_id,
                    competition_id=team.competition_id,
                    competition_name=comp.name if comp else "Unknown",
                    placement_rank=placement_rank,
                    placement_label=placement_label,
                    current_user_id=current_user_id,
                )

            # Notify: placement announcement per member
            # Commit first so data is visible to the background task's fresh session
            self._uow.commit()
            db.refresh(team)
            for m in members:
                self._notify(
                    "placement_announcement",
                    student_id=m.student_id,
                    team_id=team_id,
                    team_name=team.team_name,
                    competition_name=comp.name if comp else "Unknown",
                    placement_rank=placement_rank,
                    placement_label=placement_label,
                )


        return TeamDTO.model_validate(team) if team else None

    def _log_placement_activity(
        self,
        db,
        student_id: int,
        competition_id: int,
        competition_name: str,
        placement_rank: int,
        placement_label: Optional[str],
        current_user_id: Optional[int],
    ) -> None:
        """Log placement activity for competition result."""
        try:
            uow = UnitOfWork(db)
            activity_svc = StudentActivityService(uow)

            rank_display = placement_label if placement_label else f"{placement_rank} place"

            activity_svc._uow.activities.create_activity_log(
                student_id=student_id,
                activity_type="competition",
                activity_subtype="placement",
                reference_type="competition",
                reference_id=competition_id,
                description=f"Placed {rank_display} in '{competition_name}'",
                metadata={
                    "competition_id": competition_id,
                    "competition_name": competition_name,
                    "placement_rank": placement_rank,
                    "placement_label": placement_label,
                },
                performed_by=current_user_id,
            )
            uow.commit()
        except Exception:
            logger.exception("Failed to log placement activity for student %s, competition %s", student_id, competition_id)
