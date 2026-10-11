"""Competition fee payment and refund use cases (ADR-0006).

These workflows span finance (receipt, payment, refund), competitions (team-member
fee fields) and crm (activity log). They live in finance, the highest module
involved, and run in ONE transaction over the caller's session.
"""
import logging
from decimal import Decimal
from typing import Optional

from fastapi import BackgroundTasks
from app.db.uow import UnitOfWork
from app.modules.competitions import TeamFeeService
from app.modules.crm import LogPaymentDTO, StudentActivityService
from app.modules.finance.interfaces import CreateReceiptServiceDTO, IssueRefundDTO, RefundResultDTO
from app.modules.finance.repositories.competition_fee_repository import CompetitionFeeRepository
from app.modules.finance.repositories.unit_of_work import FinanceUnitOfWork
from app.modules.finance.schemas import ReceiptLineInput
from app.modules.finance.schemas.competition_fee import (
    PayCompetitionFeeInput,
    PayCompetitionFeeResponseDTO,
)
from app.modules.finance.services.receipt_service import ReceiptService
from app.modules.finance.services.refund_service import RefundService
from app.shared.exceptions import BusinessRuleError, NotFoundError

logger = logging.getLogger(__name__)


class CompetitionFeeService:
    def __init__(self, uow: UnitOfWork, notification_svc=None) -> None:
        self._uow = uow
        self._session = uow.session
        self._notification_svc = notification_svc
        self._repo = CompetitionFeeRepository(uow.session)
        self._team_fees = TeamFeeService(self._uow)

    # ── reads used by the HTTP layer ──────────────────────────────────────────

    def get_team_member(self, team_id: int, student_id: int):
        """Returns the TeamMember row for (team, student), or None."""
        return self._repo.get_team_member(team_id, student_id)

    # ── pay ───────────────────────────────────────────────────────────────────

    def pay_competition_fee(
        self,
        cmd: PayCompetitionFeeInput,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> PayCompetitionFeeResponseDTO:
        """
        Process a competition fee payment for a team member.
        Single atomic transaction: validation + receipt creation + fee recording
        + activity log, committed once.
        """
        team = self._repo.get_team(cmd.team_id)
        if not team:
            raise NotFoundError(f"Team {cmd.team_id} not found.")

        member = self._repo.get_team_member(cmd.team_id, cmd.student_id)
        if not member:
            raise NotFoundError(f"Student {cmd.student_id} is not a member of team {cmd.team_id}.")

        amount = cmd.amount
        if amount <= 0:
            raise BusinessRuleError("Payment amount must be greater than 0.")

        payer_name = None
        if cmd.parent_id:
            parent = self._repo.get_parent(cmd.parent_id)
            if parent:
                payer_name = parent.full_name

        with FinanceUnitOfWork(session=self._session) as finance_uow:
            result = ReceiptService(finance_uow).create(
                CreateReceiptServiceDTO(
                    lines=[
                        ReceiptLineInput(
                            student_id=cmd.student_id,
                            enrollment_id=None,
                            team_member_id=member.id,
                            amount=amount,
                            payment_type="competition",
                        )
                    ],
                    payer_name=payer_name,
                    payment_method="cash",
                    received_by_user_id=cmd.received_by_user_id,
                    allow_credit=False,
                    notes=f"Competition fee — Team #{cmd.team_id}",
                ),
                commit=False,
            )
            payment_id = result.payment_ids[0]

        self._team_fees.record_payment(member.id, amount)

        comp = self._repo.get_competition(team.competition_id)
        self._log_payment_activity(
            student_id=cmd.student_id,
            payment_id=payment_id,
            amount=amount,
            competition_name=comp.name if comp else "Unknown",
            current_user_id=cmd.received_by_user_id,
        )

        # One commit: if anything above fails, receipt, payment and fee all roll back.
        self._uow.commit()

        if self._notification_svc and background_tasks:
            self._notification_svc.competition.notify_competition_fee_paid(
                student_id=cmd.student_id,
                team_id=cmd.team_id,
                team_name=team.team_name,
                competition_name=comp.name if comp else "Unknown",
                amount=Decimal(str(amount)),
                receipt_number=result.receipt_number,
                background_tasks=background_tasks,
            )

        updated_member = self._repo.get_team_member(cmd.team_id, cmd.student_id)
        return PayCompetitionFeeResponseDTO(
            receipt_number=result.receipt_number,
            payment_id=payment_id,
            amount=amount,
            amount_paid=updated_member.amount_paid if updated_member else amount,
            amount_due=updated_member.amount_due if updated_member else 0.0,
        )

    def _log_payment_activity(
        self,
        student_id: int,
        payment_id: int,
        amount: float,
        competition_name: str,
        current_user_id: Optional[int],
    ) -> None:
        """Log the payment in the student's activity timeline; never fails the payment."""
        try:
            team_member = self._repo.get_member_of_student(student_id)
            team_id = team_member.team_id if team_member else None
            competition_id = None
            team_name = None
            if team_member:
                team_obj = self._repo.get_team(team_member.team_id)
                if team_obj:
                    competition_id = team_obj.competition_id
                    team_name = team_obj.team_name

            StudentActivityService(self._uow).log_payment(
                LogPaymentDTO(
                    student_id=student_id,
                    payment_id=payment_id,
                    amount=Decimal(str(amount)),
                    payment_type="competition_fee",
                    performed_by=current_user_id,
                    metadata={
                        "competition_id": competition_id,
                        "competition_name": competition_name,
                        "team_id": team_id,
                        "team_name": team_name,
                    },
                )
            )
        except Exception:
            logger.exception(
                "Failed to log payment activity for student %s, payment %s", student_id, payment_id
            )

    # ── refund ────────────────────────────────────────────────────────────────

    def _get_refundable_competition_payment_id(
        self, finance_uow: FinanceUnitOfWork, team_member_id: int, amount: float
    ) -> int:
        """Find the newest competition payment with enough refundable balance."""
        requested = Decimal(str(amount))
        for payment in finance_uow.payments.list_refundable_competition_payments(team_member_id):
            available = Decimal(str(payment.amount)) - finance_uow.payments.get_total_refunded(
                payment.id
            )
            if available >= requested:
                return payment.id

        raise BusinessRuleError(
            "No competition payment with enough refundable balance was found for this refund amount."
        )

    def refund_competition_fee(
        self,
        team_member_id: int,
        amount: float,
        current_user_id: Optional[int] = None,
    ) -> RefundResultDTO:
        """Refund a competition payment; receipt, refund and fee adjustment in one transaction."""
        member = self._repo.get_team_member_by_id(team_member_id)
        if not member:
            raise NotFoundError(f"Team member {team_member_id} not found.")
        if amount <= 0:
            raise BusinessRuleError("Refund amount must be greater than 0.")

        with FinanceUnitOfWork(session=self._session) as finance_uow:
            original_payment_id = self._get_refundable_competition_payment_id(
                finance_uow, team_member_id, amount
            )
            result = RefundService(finance_uow).issue(
                IssueRefundDTO(
                    payment_id=original_payment_id,
                    amount=Decimal(str(amount)),
                    reason=f"Competition fee refund for team member {team_member_id}",
                    received_by_user_id=current_user_id,
                    method="cash",
                )
            )
        self._uow.commit()
        return result
