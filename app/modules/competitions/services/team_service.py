from datetime import date
from typing import Optional
from app.db.connection import get_session
import app.modules.competitions.repositories.team_repository as team_repo
import app.modules.competitions.repositories.competition_repository as comp_repo
from app.shared.exceptions import ValidationError, NotFoundError, BusinessRuleError, ConflictError
from app.modules.competitions.schemas.team_schemas import (
    RegisterTeamInput,
    PayCompetitionFeeInput,
    TeamDTO,
    StudentCompetitionDTO,
    TeamRegistrationResultDTO,
    AddTeamMemberResultDTO,
    TeamMemberRosterDTO,
    PayCompetitionFeeResponseDTO,
    TeamMemberDTO,
)
from app.modules.competitions.schemas.competition_schemas import (
    CompetitionDTO,
    CompetitionCategoryDTO,
)


class TeamService:
    """Service layer for managing Teams and Team Members."""

    def get_student_competitions(self, student_id: int) -> list[StudentCompetitionDTO]:
        """Returns all teams a student is in, nested with category and competition info."""
        with get_session() as db:
            memberships = team_repo.list_student_memberships(db, student_id)
            result = []
            for m in memberships:
                team = team_repo.get_team(db, m.team_id)
                if not team:
                    continue
                cat = comp_repo.get_category(db, team.category_id)
                comp = comp_repo.get_competition(db, cat.competition_id) if cat else None

                result.append(
                    StudentCompetitionDTO(
                        membership=TeamMemberDTO.model_validate(m),
                        team=TeamDTO.model_validate(team),
                        category=CompetitionCategoryDTO.model_validate(cat) if cat else None,
                        competition=CompetitionDTO.model_validate(comp) if comp else None
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

    def register_team(self, cmd: RegisterTeamInput) -> TeamRegistrationResultDTO:
        """
        Creates a team and adds all listed students as members.
        Validates that all students are active before inserting anything.
        """
        from app.modules.crm.models.student_models import Student

        with get_session() as db:
            # Validate category exists
            cat = comp_repo.get_category(db, cmd.category_id)
            if not cat:
                raise NotFoundError(f"Category {cmd.category_id} not found.")

            # Validate team name uniqueness in this category
            existing_teams = team_repo.list_teams(db, cmd.category_id)
            if any(t.team_name.lower() == cmd.team_name.lower() for t in existing_teams):
                raise ConflictError(
                    f"A team named '{cmd.team_name}' already exists in this category."
                )

            # Validate all students are active
            for sid in cmd.student_ids:
                s = db.get(Student, sid)
                if not s:
                    raise NotFoundError(f"Student {sid} not found.")
                if not s.is_active:
                    raise BusinessRuleError(f"Student '{s.full_name}' is not active.")

            # Create team
            team = team_repo.create_team(
                db, 
                category_id=cmd.category_id, 
                team_name=cmd.team_name, 
                coach_id=cmd.coach_id, 
                group_id=cmd.group_id
            )

            # Fetch competition fee for member_share
            comp = comp_repo.get_competition(db, cat.competition_id)
            fee = comp.fee_per_student if comp else 0.0

            # Add members
            members_added = 0
            for sid in cmd.student_ids:
                # Skip duplicates gracefully
                existing = team_repo.get_team_member(db, team.id, sid)
                if not existing:
                    team_repo.add_team_member(db, team.id, sid, member_share=fee)
                    members_added += 1

            return TeamRegistrationResultDTO(
                team=TeamDTO.model_validate(team),
                members_added=members_added
            )

    def list_teams(self, category_id: int) -> list[TeamDTO]:
        with get_session() as db:
            teams = team_repo.list_teams(db, category_id)
            return [TeamDTO.model_validate(t) for t in teams]

    def update_team(self, team_id: int, **kwargs) -> TeamDTO | None:
        with get_session() as db:
            team = team_repo.update_team(db, team_id, **kwargs)
            return TeamDTO.model_validate(team) if team else None

    def delete_team(self, team_id: int) -> bool:
        with get_session() as db:
            return team_repo.delete_team(db, team_id)

    def add_team_member_to_existing(self, team_id: int, student_id: int) -> AddTeamMemberResultDTO:
        from app.modules.crm.models.student_models import Student

        with get_session() as db:
            team = team_repo.get_team(db, team_id)
            if not team:
                raise NotFoundError(f"Team {team_id} not found.")
            s = db.get(Student, student_id)
            if not s or not s.is_active:
                raise NotFoundError(f"Student {student_id} not found or inactive.")

            existing = team_repo.get_team_member(db, team_id, student_id)
            if existing:
                raise ConflictError(f"Student is already a member of this team.")

            cat = comp_repo.get_category(db, team.category_id)
            comp = comp_repo.get_competition(db, cat.competition_id) if cat else None
            fee = comp.fee_per_student if comp else 0.0

            m = team_repo.add_team_member(db, team_id, student_id, member_share=fee)
            return AddTeamMemberResultDTO(
                team_member_id=m.id,
                student_id=m.student_id,
                student_name=s.full_name,
            )

    def remove_team_member(self, team_id: int, student_id: int) -> bool:
        with get_session() as db:
            return team_repo.remove_team_member(db, team_id, student_id)

    def list_team_members(self, team_id: int) -> list[TeamMemberRosterDTO]:
        """Returns team members enriched with student name and fee status."""
        from app.modules.crm.models.student_models import Student

        with get_session() as db:
            members = team_repo.list_team_members(db, team_id)
            result = []
            for m in members:
                s = db.get(Student, m.student_id)
                result.append(
                    TeamMemberRosterDTO(
                        team_member_id=m.id,
                        student_id=m.student_id,
                        student_name=s.full_name if s else f"Student #{m.student_id}",
                        member_share=m.member_share,
                        fee_paid=m.fee_paid,
                        payment_id=m.payment_id,
                    )
                )
            return result

    def pay_competition_fee(self, cmd: PayCompetitionFeeInput) -> PayCompetitionFeeResponseDTO:
        from app.modules.finance import finance_service as fin_srv
        from app.modules.finance.finance_schemas import ReceiptLineInput

        with get_session() as db:
            team = team_repo.get_team(db, cmd.team_id)
            if not team:
                raise NotFoundError(f"Team {cmd.team_id} not found.")

            member = team_repo.get_team_member(db, cmd.team_id, cmd.student_id)
            if not member:
                raise NotFoundError(f"Student {cmd.student_id} is not a member of team {cmd.team_id}.")
            if member.fee_paid:
                raise BusinessRuleError("Fee is already paid for this student.")

            fee = member.member_share
            if fee <= 0:
                raise BusinessRuleError(
                    "Student's member share fee is 0."
                )

        # Trigger external finance service layer
        summary = fin_srv.create_receipt_with_charge_lines(
            parent_id=cmd.parent_id,
            method="cash",
            received_by_user_id=cmd.received_by_user_id,
            lines=[
                ReceiptLineInput(
                    student_id=cmd.student_id,
                    enrollment_id=None,
                    amount=fee,
                    payment_type="competition",
                )
            ],
            notes=f"Competition fee — Team #{cmd.team_id}",
        )
        payment_id = summary["payment_ids"][0]

        # Finalize fee status independently
        with get_session() as db:
            team_repo.mark_fee_paid(db, cmd.team_id, cmd.student_id, payment_id)

        return PayCompetitionFeeResponseDTO(
            receipt_number=summary["receipt_number"],
            payment_id=payment_id,
            amount=fee,
        )

    def unmark_team_fee_for_payment(self, payment_id: int) -> None:
        """
        Revert fee_paid status on all TeamMembers linked to a given payment.
        Called by finance when a competition payment is refunded.
        """
        with get_session() as db:
            members = team_repo.get_members_by_payment_id(db, payment_id)
            for m in members:
                m.fee_paid = False
                m.payment_id = None
                db.add(m)
