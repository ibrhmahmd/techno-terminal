from datetime import date
from typing import Optional
from app.db.connection import get_session
import app.modules.competitions.repositories.team_repository as team_repo
import app.modules.competitions.repositories.competition_repository as comp_repo
from app.shared.exceptions import NotFoundError, BusinessRuleError, ConflictError
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
    TeamWithMembersDTO,
)
from app.modules.competitions.schemas.competition_schemas import CompetitionDTO


class TeamService:
    """Service layer for managing Teams with 3-table schema."""

    def get_student_competitions(self, student_id: int) -> list[StudentCompetitionDTO]:
        """
        Returns all teams a student is in, nested with category and competition info.
        Uses 3-table schema: direct competition_id on teams.
        """
        from app.modules.crm.models.student_models import Student

        with get_session() as db:
            memberships = team_repo.list_student_memberships(db, student_id)
            result = []
            for m in memberships:
                team = team_repo.get_team(db, m.team_id)
                if not team:
                    continue

                # Direct FK to competition (no category lookup needed)
                comp = comp_repo.get_competition(db, team.competition_id)

                result.append(
                    StudentCompetitionDTO(
                        membership=TeamMemberDTO.model_validate(m),
                        team=TeamDTO.model_validate(team),
                        category=team.category,
                        subcategory=team.subcategory,
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

    def register_team(self, cmd: RegisterTeamInput, current_user_id: Optional[int] = None) -> TeamRegistrationResultDTO:
        """
        Creates a team and adds all listed students as members.
        3-table schema: uses competition_id, category, subcategory directly.
        Business rules:
        - One student can only be in one team per competition
        - If category has subcategories, must specify subcategory
        """
        from app.modules.crm.models.student_models import Student

        with get_session() as db:
            # Validate competition exists
            comp = comp_repo.get_competition(db, cmd.competition_id)
            if not comp:
                raise NotFoundError(f"Competition {cmd.competition_id} not found.")

            # Business rule: If category has subcategories, must specify subcategory
            if cmd.subcategory is None:
                has_subs = team_repo.check_category_has_subcategories(
                    db, cmd.competition_id, cmd.category
                )
                if has_subs:
                    raise BusinessRuleError(
                        f"Category '{cmd.category}' has subcategories. "
                        "Must specify a subcategory."
                    )

            # Validate team name uniqueness in this competition
            existing_teams = team_repo.list_teams(db, cmd.competition_id, cmd.category, cmd.subcategory)
            if any(t.team_name.lower() == cmd.team_name.lower() for t in existing_teams):
                raise ConflictError(
                    f"A team named '{cmd.team_name}' already exists in this category."
                )

            # Validate all students are active and not already in this competition
            for sid in cmd.student_ids:
                s = db.get(Student, sid)
                if not s:
                    raise NotFoundError(f"Student {sid} not found.")
                if s.status != "active":
                    raise BusinessRuleError(f"Student '{s.full_name}' is not active.")

                # Business rule: One student per competition
                already_enrolled = team_repo.check_student_in_competition(
                    db, cmd.competition_id, sid
                )
                if already_enrolled:
                    raise ConflictError(
                        f"Student '{s.full_name}' is already enrolled in another team "
                        f"for this competition."
                    )

            # Create team (no team-level fee — fees are per-student on TeamMember)
            team = team_repo.create_team(
                db,
                competition_id=cmd.competition_id,
                team_name=cmd.team_name,
                category=cmd.category,
                subcategory=cmd.subcategory,
                coach_id=cmd.coach_id,
                group_id=cmd.group_id,
                notes=cmd.notes,
            )

            # Add members with per-student fee from input (default 0 if not specified)
            members_added = 0
            for sid in cmd.student_ids:
                member_share = cmd.student_fees.get(sid, 0.0) if cmd.student_fees else 0.0
                # Skip duplicates gracefully
                existing = team_repo.get_team_member(db, team.id, sid)
                if not existing:
                    team_repo.add_team_member(db, team.id, sid, member_share=member_share)
                    members_added += 1

            # Auto-create group competition participation if team belongs to a group
            if cmd.group_id is not None:
                from app.shared.datetime_utils import utc_now
                from app.modules.academics.models.group_level_models import GroupCompetitionParticipation
                participation = GroupCompetitionParticipation(
                    group_id=cmd.group_id,
                    team_id=team.id,
                    competition_id=cmd.competition_id,
                    entered_at=utc_now(),
                    is_active=True,
                )
                db.add(participation)

            # Log activity and notify for each student
            self._log_team_registration_activity(
                db=db,
                team=team,
                student_ids=cmd.student_ids,
                competition_name=comp.name,
                current_user_id=current_user_id,
            )

            return TeamRegistrationResultDTO(
                team=TeamDTO.model_validate(team),
                members_added=members_added
            )

    def _log_team_registration_activity(
        self,
        db,
        team,
        student_ids: list[int],
        competition_name: str,
        current_user_id: Optional[int],
    ) -> None:
        """Log competition registration activity for each team member."""
        from app.modules.crm.repositories.unit_of_work import StudentUnitOfWork
        from app.modules.crm.services.activity_service import StudentActivityService
        from app.modules.crm.interfaces.dtos.log_competition_registration_dto import LogCompetitionRegistrationDTO

        # Create UoW and activity service
        # Note: This is a simplified integration - in production you'd want to
        # share the same transaction/session
        try:
            uow = StudentUnitOfWork(db)
            activity_svc = StudentActivityService(uow)

            for sid in student_ids:
                activity_svc.log_competition_registration(
                    LogCompetitionRegistrationDTO(
                        student_id=sid,
                        competition_id=team.competition_id,
                        competition_name=competition_name,
                        performed_by=current_user_id,
                    )
                )
            uow.commit()
        except Exception:
            # Don't fail the registration if logging fails
            # In production, you'd want to log this error somewhere
            pass

    def _log_payment_activity(
        self,
        db,
        student_id: int,
        payment_id: int,
        amount: float,
        competition_name: str,
        current_user_id: Optional[int],
    ) -> None:
        """Log payment activity for competition fee."""
        from app.modules.crm.repositories.unit_of_work import StudentUnitOfWork
        from app.modules.crm.services.activity_service import StudentActivityService
        from app.modules.crm.interfaces.dtos.log_payment_dto import LogPaymentDTO
        from decimal import Decimal

        try:
            uow = StudentUnitOfWork(db)
            activity_svc = StudentActivityService(uow)

            activity_svc.log_payment(
                LogPaymentDTO(
                    student_id=student_id,
                    payment_id=payment_id,
                    amount=Decimal(str(amount)),
                    payment_type="competition_fee",
                    performed_by=current_user_id,
                )
            )
            uow.commit()
        except Exception:
            # Don't fail the payment if logging fails
            pass

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
        from app.modules.crm.repositories.unit_of_work import StudentUnitOfWork
        from app.modules.crm.services.activity_service import StudentActivityService

        try:
            uow = StudentUnitOfWork(db)
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
            # Don't fail if logging fails
            pass

    def get_team_by_id(self, team_id: int) -> TeamDTO | None:
        """Get a single team by ID."""
        with get_session() as db:
            team = team_repo.get_team(db, team_id)
            return TeamDTO.model_validate(team) if team else None

    def list_teams(
        self,
        competition_id: int,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
    ) -> list[TeamDTO]:
        """List teams for a competition with optional filters."""
        with get_session() as db:
            teams = team_repo.list_teams(db, competition_id, category, subcategory)
            return [TeamDTO.model_validate(t) for t in teams]

    def get_teams_with_members(
        self,
        competition_id: int,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
    ) -> list[TeamWithMembersDTO]:
        """Returns all teams with their members."""
        with get_session() as db:
            teams = team_repo.list_teams(db, competition_id, category, subcategory)
            result = []
            for team in teams:
                members = team_repo.list_team_members(db, team.id)
                result.append(
                    TeamWithMembersDTO(
                        team=TeamDTO.model_validate(team),
                        members=[TeamMemberDTO.model_validate(m) for m in members]
                    )
                )
            return result

    def update_team(self, team_id: int, **kwargs) -> TeamDTO | None:
        """Update team fields."""
        with get_session() as db:
            team = team_repo.update_team(db, team_id, **kwargs)
            return TeamDTO.model_validate(team) if team else None

    def delete_team(self, team_id: int, deleted_by: Optional[int] = None) -> bool:
        """Soft delete a team."""
        with get_session() as db:
            # Check if any member has paid fees
            members = team_repo.list_team_members(db, team_id)
            for m in members:
                if m.fee_paid:
                    raise BusinessRuleError(
                        "Cannot delete team with members who have paid fees."
                    )
            return team_repo.delete_team(db, team_id, deleted_by=deleted_by)

    def restore_team(self, team_id: int) -> bool:
        """Restore a soft-deleted team."""
        with get_session() as db:
            return team_repo.restore_team(db, team_id)

    def list_deleted_teams(self, competition_id: Optional[int] = None) -> list[TeamDTO]:
        """List soft-deleted teams."""
        with get_session() as db:
            teams = team_repo.list_deleted_teams(db, competition_id)
            return [TeamDTO.model_validate(t) for t in teams]

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
        with get_session() as db:
            team = team_repo.get_team(db, team_id)
            if not team:
                raise NotFoundError(f"Team {team_id} not found.")

            comp = comp_repo.get_competition(db, team.competition_id)
            if comp and comp.competition_date and comp.competition_date > date.today():
                raise BusinessRuleError(
                    "Cannot set placement before competition date"
                )

            team = team_repo.update_team(
                db, team_id,
                placement_rank=placement_rank,
                placement_label=placement_label
            )

            # Sync placement to active group competition participation
            from sqlalchemy import select
            from app.modules.academics.models.group_level_models import GroupCompetitionParticipation
            stmt = select(GroupCompetitionParticipation).where(
                GroupCompetitionParticipation.team_id == team_id,
                GroupCompetitionParticipation.is_active == True,
            )
            active_participation = db.exec(stmt).first()
            if active_participation:
                active_participation.final_placement = placement_rank
                db.add(active_participation)

            # Log activity for each team member
            if team:
                members = team_repo.list_team_members(db, team_id)
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

            return TeamDTO.model_validate(team) if team else None

    def add_team_member_to_existing(
        self,
        team_id: int,
        student_id: int,
        fee: float = 0.0,
        current_user_id: Optional[int] = None,
    ) -> AddTeamMemberResultDTO:
        """Add a student to an existing team."""
        from app.modules.crm.models.student_models import Student

        with get_session() as db:
            team = team_repo.get_team(db, team_id)
            if not team:
                raise NotFoundError(f"Team {team_id} not found.")

            # Check if student already in this competition
            already_enrolled = team_repo.check_student_in_competition(
                db, team.competition_id, student_id
            )
            if already_enrolled:
                raise ConflictError(
                    "Student is already enrolled in another team for this competition."
                )

            s = db.get(Student, student_id)
            if not s or not s.is_active:
                raise NotFoundError(f"Student {student_id} not found or inactive.")

            existing = team_repo.get_team_member(db, team_id, student_id)
            if existing:
                raise ConflictError("Student is already a member of this team.")

            m = team_repo.add_team_member(db, team_id, student_id, member_share=fee)

            # Log activity for student joining team
            comp = comp_repo.get_competition(db, team.competition_id)
            self._log_team_registration_activity(
                db=db,
                team=team,
                student_ids=[student_id],
                competition_name=comp.name if comp else "Unknown",
                current_user_id=current_user_id,
            )

            return AddTeamMemberResultDTO(
                team_member_id=m.id,
                student_id=m.student_id,
                student_name=s.full_name,
            )

    def remove_team_member(self, team_id: int, student_id: int) -> bool:
        with get_session() as db:
            # Check if member has already paid - cannot remove paid members
            member = team_repo.get_team_member(db, team_id, student_id)
            if member and member.fee_paid:
                raise BusinessRuleError(
                    "Cannot remove a team member who has already paid the competition fee."
                )
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
        from app.modules.finance.repositories.unit_of_work import FinanceUnitOfWork
        from app.modules.finance.services.receipt_service import ReceiptService
        from app.modules.finance import ReceiptLineInput
        from app.modules.crm.models.parent_models import Parent

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

            # Fetch parent name if parent_id provided
            payer_name = None
            if cmd.parent_id:
                parent = db.get(Parent, cmd.parent_id)
                if parent:
                    payer_name = parent.full_name

        # Use new SOLID-compliant ReceiptService
        with FinanceUnitOfWork() as uow:
            service = ReceiptService(uow)
            result = service.create(
                lines=[
                    ReceiptLineInput(
                        student_id=cmd.student_id,
                        enrollment_id=None,
                        amount=fee,
                        payment_type="competition",
                    )
                ],
                payer_name=payer_name,
                payment_method="cash",
                received_by_user_id=cmd.received_by_user_id,
                allow_credit=False,
                notes=f"Competition fee — Team #{cmd.team_id}",
            )
            payment_id = result.payment_ids[0]

        # Finalize fee status independently
        try:
            with get_session() as db:
                team_repo.mark_fee_paid(db, cmd.team_id, cmd.student_id, payment_id)

                # Log payment activity
                team = team_repo.get_team(db, cmd.team_id)
                comp = comp_repo.get_competition(db, team.competition_id) if team else None
                self._log_payment_activity(
                    db=db,
                    student_id=cmd.student_id,
                    payment_id=payment_id,
                    amount=fee,
                    competition_name=comp.name if comp else "Unknown",
                    current_user_id=cmd.received_by_user_id,
                )
        except Exception as e:
            # Rollback: refund the payment if fee marking fails
            with FinanceUnitOfWork() as uow:
                refund_service = ReceiptService(uow)
                refund_service.refund_payment(
                    payment_id=payment_id,
                    reason="Failed to mark competition fee as paid",
                    processed_by_user_id=cmd.received_by_user_id,
                )
            raise BusinessRuleError(
                f"Payment created but failed to mark fee as paid. Payment has been refunded. Error: {e}"
            )

        return PayCompetitionFeeResponseDTO(
            receipt_number=result.receipt_number,
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
            db.commit()
