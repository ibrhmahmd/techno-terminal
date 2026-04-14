"""
app/modules/finance/services/partial_payment_service.py
────────────────────────────────────────────────────────
Partial payment allocation and management service.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlmodel import Session, select, func

from app.db.connection import get_session
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.finance.models.finance_models import Payment, Receipt
from app.modules.finance.models.balance_models import (
    PaymentAllocation,
    PaymentAllocationInput,
    PaymentAllocationResponse,
    StudentCredit,
)
from app.api.schemas.finance.credit import (
    CreditApplicationItem,
    ApplyCreditResponse,
)
from app.api.schemas.finance.allocations import AllocationReversalResponse
from app.shared.errors import NotFoundError, BusinessRuleError


class PartialPaymentService:
    """Service for managing partial payments and allocations."""
    
    def __init__(self, db = None):
        """Initialize with optional database session."""
        self._db = db
        self._own_session = db is None
    
    def _get_db(self):
        """Get or create database session."""
        if self._db is None:
            self._db = get_session().__enter__()
        return self._db
    
    def __del__(self):
        """Cleanup session if owned."""
        if self._own_session and self._db:
            self._db.close()
    
    def allocate_payment(
        self,
        student_id: int,
        payment_id: int,
        amount: Decimal,
        allocation_strategy: str = 'oldest_first',
        target_enrollment_ids: Optional[List[int]] = None,
        performed_by: Optional[int] = None
    ) -> PaymentAllocationResponse:
        """
        Allocate a payment across student enrollments.
        
        Strategies:
        - oldest_first: Apply to oldest unpaid enrollments first
        - largest_debt: Apply to enrollment with largest remaining balance
        - manual: Use specified target_enrollment_ids
        
        Args:
            student_id: The student receiving the payment
            payment_id: The payment being allocated
            amount: Total amount to allocate
            allocation_strategy: How to distribute the payment
            target_enrollment_ids: Specific enrollment IDs (for manual strategy)
            performed_by: User ID performing the allocation
            
        Returns:
            PaymentAllocationResponse with allocation details
        """
        db = self._get_db()
        
        # Verify payment exists and belongs to student
        payment = db.get(Payment, payment_id)
        if not payment:
            raise NotFoundError(f"Payment with ID {payment_id} not found")
        
        if payment.student_id != student_id:
            raise BusinessRuleError(f"Payment does not belong to student {student_id}")
        
        remaining = Decimal(str(amount))
        allocations = []
        
        # Get enrollments to allocate against
        if allocation_strategy == 'manual' and target_enrollment_ids:
            enrollments = self._get_specific_enrollments(target_enrollment_ids, db)
        else:
            enrollments = self._get_unpaid_enrollments(student_id, allocation_strategy, db)
        
        # Allocate to each enrollment
        for enrollment in enrollments:
            if remaining <= 0:
                break
            
            # Calculate remaining balance for this enrollment
            current_balance = self._get_enrollment_remaining_balance(enrollment.id, db)
            
            if current_balance <= 0:
                continue  # Already paid
            
            # Allocate up to remaining balance or payment remainder
            allocate_amount = min(remaining, current_balance)
            
            allocation = PaymentAllocation(
                payment_id=payment_id,
                enrollment_id=enrollment.id,
                allocated_amount=float(allocate_amount),
                allocation_type='course_fee',
                allocated_at=datetime.utcnow(),
                allocated_by=performed_by,
                notes=f'Auto-allocated via {allocation_strategy}'
            )
            
            db.add(allocation)
            db.flush()  # Get the ID
            allocations.append(allocation)
            remaining -= allocate_amount
        
        # Handle overpayment (credit)
        credit_applied = False
        if remaining > 0:
            # Create credit allocation
            credit_allocation = PaymentAllocation(
                payment_id=payment_id,
                enrollment_id=None,
                allocated_amount=float(remaining),
                allocation_type='credit',
                allocated_at=datetime.utcnow(),
                allocated_by=performed_by,
                notes='Credit applied to student account'
            )
            db.add(credit_allocation)
            db.flush()
            allocations.append(credit_allocation)
            
            # Create student credit record
            credit = StudentCredit(
                student_id=student_id,
                payment_id=payment_id,
                credit_amount=float(remaining),
                status='active',
                created_at=datetime.utcnow()
            )
            db.add(credit)
            credit_applied = True
        
        db.commit()
        
        return PaymentAllocationResponse(
            payment_id=payment_id,
            total_allocated=float(amount - remaining),
            credit_remaining=float(remaining),
            allocations=allocations,
            credit_applied=credit_applied
        )
    
    def _get_unpaid_enrollments(
        self,
        student_id: int,
        strategy: str,
        db: Session
    ) -> List[Enrollment]:
        """Get unpaid enrollments ordered by strategy."""
        
        base_query = select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.status.in_(['active', 'completed'])
        )
        
        if strategy == 'oldest_first':
            query = base_query.order_by(Enrollment.enrolled_at.asc())
        elif strategy == 'largest_debt':
            # Get all enrollments and sort by remaining balance
            enrollments = db.exec(base_query).all()
            enrollments_with_balance = []
            
            for enrollment in enrollments:
                remaining = self._get_enrollment_remaining_balance(enrollment.id, db)
                if remaining > 0:
                    enrollments_with_balance.append((enrollment, remaining))
            
            # Sort by remaining balance descending
            enrollments_with_balance.sort(key=lambda x: x[1], reverse=True)
            return [e[0] for e in enrollments_with_balance]
        else:
            # Default to oldest first
            query = base_query.order_by(Enrollment.enrolled_at.asc())
        
        return db.exec(query).all()
    
    def _get_specific_enrollments(
        self,
        enrollment_ids: List[int],
        db: Session
    ) -> List[Enrollment]:
        """Get specific enrollments by ID."""
        enrollments = []
        for eid in enrollment_ids:
            enrollment = db.get(Enrollment, eid)
            if enrollment:
                enrollments.append(enrollment)
        return enrollments
    
    def _get_enrollment_remaining_balance(self, enrollment_id: int, db: Session) -> Decimal:
        """Calculate remaining balance for an enrollment."""
        enrollment = db.get(Enrollment, enrollment_id)
        if not enrollment:
            return Decimal('0.00')
        
        due = Decimal(str(enrollment.amount_due or 0))
        discount = Decimal(str(enrollment.discount_applied or 0))
        
        # Get total paid through allocations
        result = db.exec(
            select(func.sum(PaymentAllocation.allocated_amount))
            .join(Payment, PaymentAllocation.payment_id == Payment.id)
            .where(PaymentAllocation.enrollment_id == enrollment_id)
            .where(Payment.transaction_type == 'payment')
        ).first()
        
        paid = Decimal(str(result[0] or 0)) if result and result[0] else Decimal('0.00')
        
        return due - discount - paid
    
    def apply_credit_to_enrollment(
        self,
        student_id: int,
        enrollment_id: int,
        amount: Optional[Decimal] = None,
        performed_by: Optional[int] = None
    ) -> ApplyCreditResponse:
        """
        Apply available credit to a specific enrollment.
        
        Args:
            student_id: Student with credit
            enrollment_id: Enrollment to apply credit to
            amount: Specific amount to apply (default: all available credit)
            performed_by: User performing the action
            
        Returns:
            ApplyCreditResponse with credit application details
        """
        db = self._get_db()
        
        # Get available credits
        credits = db.exec(
            select(StudentCredit)
            .where(StudentCredit.student_id == student_id)
            .where(StudentCredit.status == 'active')
            .where(StudentCredit.remaining_credit > 0)
            .order_by(StudentCredit.created_at.asc())  # Oldest first
        ).all()
        
        if not credits:
            raise BusinessRuleError(f"No available credit for student {student_id}")
        
        total_available = sum(Decimal(str(c.remaining_credit)) for c in credits)
        
        # Determine amount to apply
        apply_amount = amount if amount else total_available
        apply_amount = min(apply_amount, total_available)
        
        # Get enrollment remaining balance
        remaining_balance = self._get_enrollment_remaining_balance(enrollment_id, db)
        
        if remaining_balance <= 0:
            raise BusinessRuleError("Enrollment is already fully paid")
        
        # Apply up to the remaining balance
        apply_amount = min(apply_amount, remaining_balance)
        
        # Track applications
        applications = []
        remaining_to_apply = apply_amount
        
        for credit in credits:
            if remaining_to_apply <= 0:
                break
            
            credit_remaining = Decimal(str(credit.remaining_credit))
            use_from_this = min(remaining_to_apply, credit_remaining)
            
            # Update credit
            credit.used_amount = float(Decimal(str(credit.used_amount)) + use_from_this)
            if credit.used_amount >= credit.credit_amount:
                credit.status = 'used'
            
            db.add(credit)
            
            applications.append(CreditApplicationItem(
                credit_id=credit.id,
                amount_applied=float(use_from_this),
                credit_remaining=float(Decimal(str(credit.credit_amount)) - Decimal(str(credit.used_amount)))
            ))
            
            remaining_to_apply -= use_from_this
        
        # Create allocation record
        # Note: This would typically need a payment record, which doesn't exist for credit application
        # For now, we'll just track it in the credit records
        
        db.commit()
        
        return ApplyCreditResponse(
            student_id=student_id,
            enrollment_id=enrollment_id,
            amount_applied=float(apply_amount),
            credit_applications=applications,
            enrollment_balance_after=float(remaining_balance - apply_amount),
            applied_at=datetime.utcnow(),
            applied_by=performed_by
        )
    
    def get_payment_allocations(self, payment_id: int) -> List[PaymentAllocation]:
        """Get all allocations for a specific payment."""
        db = self._get_db()
        
        allocations = db.exec(
            select(PaymentAllocation)
            .where(PaymentAllocation.payment_id == payment_id)
            .order_by(PaymentAllocation.allocated_at.desc())
        ).all()
        
        return allocations
    
    def reverse_allocation(
        self,
        allocation_id: int,
        reason: str,
        performed_by: Optional[int] = None
    ) -> AllocationReversalResponse:
        """
        Reverse a payment allocation (for refunds/corrections).
        
        Args:
            allocation_id: The allocation to reverse
            reason: Reason for reversal
            performed_by: User performing the reversal
            
        Returns:
            AllocationReversalResponse with reversal details
        """
        db = self._get_db()
        
        allocation = db.get(PaymentAllocation, allocation_id)
        if not allocation:
            raise NotFoundError(f"Allocation with ID {allocation_id} not found")
        
        # Create reversal record
        reversal = PaymentAllocation(
            payment_id=allocation.payment_id,
            enrollment_id=allocation.enrollment_id,
            allocated_amount=-allocation.allocated_amount,  # Negative for reversal
            allocation_type='reversal',
            allocated_at=datetime.utcnow(),
            allocated_by=performed_by,
            notes=f'Reversal of allocation {allocation_id}: {reason}'
        )
        
        db.add(reversal)
        db.commit()
        
        return AllocationReversalResponse(
            original_allocation_id=allocation_id,
            reversal_allocation_id=reversal.id,
            amount_reversed=allocation.allocated_amount,
            reason=reason,
            reversed_at=datetime.utcnow(),
            reversed_by=performed_by
        )


def get_partial_payment_service(db = None):
    """Factory function to create PartialPaymentService instance."""
    return PartialPaymentService(db)
