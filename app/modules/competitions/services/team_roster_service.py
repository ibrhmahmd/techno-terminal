from datetime import date
from typing import Optional
from app.shared.exceptions import NotFoundError, BusinessRuleError, ConflictError
from app.modules.competitions.schemas.team_schemas import (
    StudentCompetitionDTO,
    AddTeamMemberResultDTO,
    AddTeamMemberResultWithWarningDTO,
    TeamMemberRosterDTO,
    TeamMemberDTO,
)
from app.modules.competitions.models.team_models import Team
from app.modules.crm.models.student_models import Student
from app.modules.competitions.services.team_base import TeamServiceBase


class TeamRosterService(TeamServiceBase):
    """Team roster use cases: members and student participation."""

    def get_student_competitions(self, student_id: int) -> list[StudentCompetitionDTO]:
        """
        Returns all teams a student is in, nested with category and competition info.
        Uses batch loading: single JOIN query instead of N+1.
        """
        rows = self._teams.list_student_memberships_enriched(student_id)

        result = []
        for row in rows:
            result.append(
                StudentCompetitionDTO(
                    membership=row.membership,
                    team=row.team,
                    category=row.team.category,
                    subcategory=row.team.subcategory,
                    competition=row.competition
                )
            )

        # Sort by competition date descending
        result.sort(
            key=lambda x: (
                x.competition.competition_date
                if x.competition and x.competition.competition_date
                else date.min
            ),
            reverse=True,
        )
        return result

    def add_team_member_to_existing(
        self,
        team_id: int,
        student_id: int,
        amount_due: Optional[float] = None,
        current_user_id: Optional[int] = None,
    ) -> AddTeamMemberResultWithWarningDTO:
        """Add a student to an existing team. Returns (result, warning_or_None)."""
        db = self._uow.session
        team = self._teams.get_team(team_id)
        if not team:
            raise NotFoundError(f"Team {team_id} not found.")

        warning = None
        # Check if student already in this competition — warn but allow
        already_enrolled = self._teams.check_student_in_competition(team.competition_id, student_id
        )
        if already_enrolled:
            s_check = db.get(Student, student_id)
            warning = (
                f"Student '{s_check.full_name if s_check else student_id}' "
                "is already enrolled in another team for this competition."
            )

        s = db.get(Student, student_id)
        if not s or not s.is_active:
            raise NotFoundError(f"Student {student_id} not found or inactive.")

        existing = self._teams.get_team_member(team_id, student_id)
        if existing:
            raise ConflictError("Student is already a member of this team.")

        if amount_due is None:
            comp = self._comps.get_competition(team.competition_id)
            amount_due = float(comp.fee_per_student or 0.0)

        m = self._teams.add_team_member(team_id, student_id, amount_due=amount_due)

        # Log activity for student joining team
        comp = self._comps.get_competition(team.competition_id)
        self._log_team_registration_activity(
            db=db,
            team=team,
            student_ids=[student_id],
            competition_name=comp.name if comp else "Unknown",
            current_user_id=current_user_id,
        )

        # Notify: team registration for added member
        # Commit first so data is visible to the background task's fresh session
        self._uow.commit()
        db.refresh(m)
        self._notify(
            "team_registration",
            student_id=student_id,
            team_id=team_id,
            team_name=team.team_name,
            competition_name=comp.name if comp else "Unknown",
            category=team.category,
            subcategory=team.subcategory,
        )


        return AddTeamMemberResultWithWarningDTO(
            result=AddTeamMemberResultDTO(
                team_member_id=m.id,
                student_id=m.student_id,
                student_name=s.full_name,
            ),
            warning=warning,
        )

    def get_team_member(self, team_id: int, student_id: int) -> TeamMemberDTO | None:
        """Returns a single team member by team_id and student_id, or None."""
        member = self._teams.get_team_member(team_id, student_id)
        return TeamMemberDTO.model_validate(member) if member else None

    def remove_team_member(self, team_id: int, student_id: int) -> bool:
        member = self._teams.get_team_member(team_id, student_id)
        if member and member.amount_paid > 0:
            raise BusinessRuleError(
                "Cannot remove a team member who has already paid the competition fee."
            )
        result = self._teams.remove_team_member(team_id, student_id)
        self._uow.commit()
        return result

    def list_team_members(self, team_id: int) -> list[TeamMemberRosterDTO]:
        """Returns team members enriched with student name and fee status. Uses batch loading."""
        db = self._uow.session
        team = db.get(Team, team_id)
        team_name = team.team_name if team else "Unknown"

        members_by_team = self._teams.list_team_members_with_students([team_id])
        member_rows = members_by_team.get(team_id, [])

        return [
            TeamMemberRosterDTO(
                team_member_id=mwr.member.id,
                team_id=team_id,
                team_name=team_name,
                student_id=mwr.member.student_id,
                student_name=mwr.student_name,
                amount_due=mwr.member.amount_due,
                amount_paid=mwr.member.amount_paid,
            )
            for mwr in member_rows
        ]
