"""
app/modules/finance/services/balance_service.py
──────────────────────────────────────────────
Balance service implementation for enrollment/student balance queries.
"""
from decimal import Decimal
from typing import Optional, List

from app.modules.finance.interfaces import (
    IBalanceService,
    OverpaymentRiskItem,
    StudentBalanceSummaryDTO,
    PaginatedEnrollmentBalancesDTO,
)
from app.modules.finance import ReceiptLineInput, EnrollmentBalanceItem
from app.modules.finance.repositories.unit_of_work import FinanceUnitOfWork


class BalanceService(IBalanceService):
    """
    Service for balance calculation operations.
    
    Responsible for:
    - Enrollment balance queries
    - Student balance summaries
    - Overpayment risk assessment
    """

    def __init__(self, uow: FinanceUnitOfWork) -> None:
        self._uow = uow

    def get_enrollment_balance(
        self, enrollment_id: int
    ) -> Optional[EnrollmentBalanceItem]:
        """Get balance details for a specific enrollment."""
        balance_dto = self._uow.payments.get_enrollment_balance(enrollment_id)

        if not balance_dto:
            return None

        return EnrollmentBalanceItem(
            enrollment_id=balance_dto.enrollment_id,
            student_id=balance_dto.student_id,
            group_id=balance_dto.group_id,
            level_number=balance_dto.level_number,
            amount_due=float(balance_dto.amount_due),
            discount_applied=float(balance_dto.discount_applied),
            amount_paid=float(balance_dto.amount_paid),
            remaining_balance=float(balance_dto.balance),
            status=balance_dto.status,
        )

    def get_student_balance_summary(
        self, student_id: int
    ) -> StudentBalanceSummaryDTO:
        """
        Get aggregated balance summary for a student.

        Returns StudentBalanceSummaryDTO containing:
        - Aggregated totals (amount_due, discounts, paid, net_balance)
        - Enrollment counts (total and unpaid)
        - Full list of enrollment balances (enrollments field)
        """
        enrollments = self._uow.payments.get_student_balances(student_id)
        
        total_amount_due = sum(e.amount_due for e in enrollments)
        total_discounts = sum(e.discount_applied for e in enrollments)
        total_paid = sum(e.amount_paid for e in enrollments)
        net_balance = sum(e.remaining_balance for e in enrollments)
        
        # Count unpaid (remaining_balance < 0 means debt)
        unpaid_count = sum(1 for e in enrollments if e.remaining_balance < 0)
        
        return StudentBalanceSummaryDTO(
            student_id=student_id,
            total_amount_due=total_amount_due,
            total_discounts=total_discounts,
            total_paid=total_paid,
            net_balance=net_balance,
            enrollment_count=len(enrollments),
            unpaid_enrollments=unpaid_count,
            enrollments=enrollments,
        )

    def get_unpaid_enrollments(
        self,
        group_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> PaginatedEnrollmentBalancesDTO:
        """
        Get all unpaid enrollments with pagination.
        Returns PaginatedEnrollmentBalancesDTO with items and total count.
        """
        items, total = self._uow.payments.get_unpaid_enrollments(
            group_id=group_id, skip=skip, limit=limit
        )
        return PaginatedEnrollmentBalancesDTO(items=items, total=total)

    def assess_overpayment_risk(
        self, lines: List[ReceiptLineInput]
    ) -> List[OverpaymentRiskItem]:
        """
        Assess which receipt lines would create credit/overpayment.
        Returns lines where projected balance after payment would be positive
        (indicating credit/overpayment).
        """
        risks: List[OverpaymentRiskItem] = []

        for line in lines:
            if not line.enrollment_id:
                continue

            balance_dto = self._uow.payments.get_enrollment_balance(line.enrollment_id)
            if not balance_dto:
                continue

            current_balance = balance_dto.balance
            pay_amount = Decimal(str(line.amount))
            projected_balance = current_balance + pay_amount

            if projected_balance > 0:
                debt_before = max(-current_balance, Decimal("0"))
                risks.append(
                    OverpaymentRiskItem(
                        student_id=line.student_id,
                        enrollment_id=line.enrollment_id,
                        amount=pay_amount,
                        debt_before=debt_before,
                        projected_balance=projected_balance,
                        excess_credit=max(pay_amount - debt_before, Decimal("0")),
                    )
                )

        return risks