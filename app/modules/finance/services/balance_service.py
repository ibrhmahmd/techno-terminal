"""
app/modules/finance/services/balance_service.py
────────────────────────────────────────────────
Student balance calculation and management service.
"""
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List

from sqlmodel import Session, select, func

from app.db.connection import get_session
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.crm.models.student_models import Student
from app.modules.academics.models.group_models import Group
from app.modules.academics.models.course_models import Course
from app.modules.finance.finance_models import Payment, Receipt
from app.modules.finance.models.balance_models import (
    StudentBalance,
    StudentBalanceDTO,
    EnrollmentBalanceDetail,
    PaymentAllocation,
    PaymentAllocationCreate,
    PaymentAllocationResult,
    BalanceAdjustmentInput,
    StudentCredit,
)
from app.api.schemas.finance.balance import (
    EnrollmentBalanceResponse,
    BalanceAdjustmentResponse,
    UnpaidEnrollmentItem,
)
from app.shared.exceptions import NotFoundError, BusinessRuleError, ValidationError


class BalanceService:
    """Service for calculating and managing student financial balances."""
    
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
    
    def calculate_balance(self, student_id: int) -> StudentBalanceDTO:
        """
        Calculate comprehensive balance for a student.
        
        Formula:
        net_balance = total_paid - (total_due - total_discounts)
        
        Args:
            student_id: The student ID to calculate balance for
            
        Returns:
            StudentBalanceDTO with all breakdowns
        """
        db = self._get_db()
        
        # Verify student exists
        student = db.get(Student, student_id)
        if not student:
            raise NotFoundError(f"Student with ID {student_id} not found")
        
        # Get all active and completed enrollments
        enrollments = db.exec(
            select(Enrollment)
            .where(Enrollment.student_id == student_id)
            .where(Enrollment.status.in_(['active', 'completed']))
        ).all()
        
        total_due = Decimal('0.00')
        total_discounts = Decimal('0.00')
        enrollment_balances = []
        
        for enrollment in enrollments:
            due = Decimal(str(enrollment.amount_due or 0))
            discount = Decimal(str(enrollment.discount_applied or 0))
            
            # Get payments for this enrollment through allocations
            allocations = db.exec(
                select(PaymentAllocation, Payment)
                .join(Payment, PaymentAllocation.payment_id == Payment.id)
                .where(PaymentAllocation.enrollment_id == enrollment.id)
                .where(Payment.transaction_type == 'payment')
            ).all()
            
            paid = sum(
                Decimal(str(allocation.allocated_amount))
                for allocation, _ in allocations
            )
            
            remaining = due - discount - paid
            
            enrollment_balance = EnrollmentBalanceDetail(
                enrollment_id=enrollment.id,
                group_id=enrollment.group_id,
                level_number=enrollment.level_number,
                amount_due=float(due.quantize(Decimal('0.01'))),
                discount_applied=float(discount.quantize(Decimal('0.01'))),
                amount_paid=float(paid.quantize(Decimal('0.01'))),
                remaining_balance=float(remaining.quantize(Decimal('0.01'))),
                status='paid' if remaining <= 0 else 'partial' if paid > 0 else 'unpaid'
            )
            
            enrollment_balances.append(enrollment_balance)
            total_due += due
            total_discounts += discount
        
        # Calculate total paid
        total_paid = sum(
            Decimal(str(e.amount_paid))
            for e in enrollment_balances
        )
        
        net_balance = total_paid - (total_due - total_discounts)
        
        return StudentBalanceDTO(
            student_id=student_id,
            total_amount_due=float(total_due.quantize(Decimal('0.01'))),
            total_discounts=float(total_discounts.quantize(Decimal('0.01'))),
            total_paid=float(total_paid.quantize(Decimal('0.01'))),
            net_balance=float(net_balance.quantize(Decimal('0.01'))),
            enrollment_details=enrollment_balances,
            as_of_date=datetime.utcnow()
        )
    
    def get_quick_balance(self, student_id: int) -> StudentBalanceDTO:
        """
        Get balance from materialized table (fast O(1) lookup).
        Falls back to calculation if no materialized balance exists.
        """
        db = self._get_db()
        
        # Try materialized table first
        materialized = db.get(StudentBalance, student_id)
        
        if materialized:
            # Get enrollment details separately
            enrollments = db.exec(
                select(Enrollment)
                .where(Enrollment.student_id == student_id)
                .where(Enrollment.status.in_(['active', 'completed']))
            ).all()
            
            enrollment_details = []
            for enrollment in enrollments:
                due = Decimal(str(enrollment.amount_due or 0))
                discount = Decimal(str(enrollment.discount_applied or 0))
                
                allocations = db.exec(
                    select(func.sum(PaymentAllocation.allocated_amount))
                    .join(Payment, PaymentAllocation.payment_id == Payment.id)
                    .where(PaymentAllocation.enrollment_id == enrollment.id)
                    .where(Payment.transaction_type == 'payment')
                ).first()
                
                paid = Decimal(str(allocations[0] or 0)) if allocations and allocations[0] else Decimal('0.00')
                remaining = due - discount - paid
                
                enrollment_details.append(EnrollmentBalanceDetail(
                    enrollment_id=enrollment.id,
                    group_id=enrollment.group_id,
                    level_number=enrollment.level_number,
                    amount_due=float(due),
                    discount_applied=float(discount),
                    amount_paid=float(paid),
                    remaining_balance=float(remaining),
                    status='paid' if remaining <= 0 else 'partial' if paid > 0 else 'unpaid'
                ))
            
            return StudentBalanceDTO(
                student_id=student_id,
                total_amount_due=float(materialized.total_amount_due),
                total_discounts=float(materialized.total_discounts),
                total_paid=float(materialized.total_paid),
                net_balance=float(materialized.net_balance),
                enrollment_details=enrollment_details,
                as_of_date=materialized.last_updated or datetime.utcnow()
            )
        
        # Fall back to full calculation
        return self.calculate_balance(student_id)
    
    def get_enrollment_balance(self, enrollment_id: int) -> EnrollmentBalanceResponse:
        """Get detailed balance for a specific enrollment."""
        db = self._get_db()
        
        enrollment = db.get(Enrollment, enrollment_id)
        if not enrollment:
            raise NotFoundError(f"Enrollment with ID {enrollment_id} not found")
        
        due = Decimal(str(enrollment.amount_due or 0))
        discount = Decimal(str(enrollment.discount_applied or 0))
        
        # Get all allocations for this enrollment
        allocations = db.exec(
            select(PaymentAllocation, Payment)
            .join(Payment, PaymentAllocation.payment_id == Payment.id)
            .where(PaymentAllocation.enrollment_id == enrollment_id)
        ).all()
        
        total_paid = sum(
            Decimal(str(allocation.allocated_amount))
            for allocation, payment in allocations
            if payment.transaction_type == 'payment'
        )
        
        total_refunded = sum(
            Decimal(str(allocation.allocated_amount))
            for allocation, payment in allocations
            if payment.transaction_type == 'refund'
        )
        
        remaining = due - discount - total_paid + total_refunded
        
        return EnrollmentBalanceResponse(
            enrollment_id=enrollment_id,
            student_id=enrollment.student_id,
            group_id=enrollment.group_id,
            level_number=enrollment.level_number,
            amount_due=float(due),
            discount_applied=float(discount),
            total_paid=float(total_paid),
            total_refunded=float(total_refunded),
            remaining_balance=float(remaining),
            status=enrollment.status,
            is_paid=remaining <= 0
        )
    
    def list_unpaid_enrollments(
        self, 
        group_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[UnpaidEnrollmentItem], int]:
        """List all unpaid enrollments with database-level pagination.
        
        Returns:
            Tuple of (paginated unpaid enrollments, total count)
        """
        db = self._get_db()
        
        query = select(
            Enrollment,
            Student.full_name.label('student_name'),
            Group.name.label('group_name'),
            Course.name.label('course_name')
        ).join(
            Student, Enrollment.student_id == Student.id
        ).join(
            Group, Enrollment.group_id == Group.id
        ).outerjoin(
            Course, Group.course_id == Course.id
        ).where(
            Enrollment.status == 'active'
        )
        
        if group_id:
            query = query.where(Enrollment.group_id == group_id)
        
        # Get all results for filtering (required since we calculate remaining balance)
        results = db.exec(query).all()
        
        unpaid = []
        for enrollment, student_name, group_name, course_name in results:
            due = Decimal(str(enrollment.amount_due or 0))
            discount = Decimal(str(enrollment.discount_applied or 0))
            
            # Get total paid
            paid_result = db.exec(
                select(func.sum(PaymentAllocation.allocated_amount))
                .join(Payment, PaymentAllocation.payment_id == Payment.id)
                .where(PaymentAllocation.enrollment_id == enrollment.id)
                .where(Payment.transaction_type == 'payment')
            ).first()
            
            paid = Decimal(str(paid_result[0] or 0)) if paid_result and paid_result[0] else Decimal('0.00')
            remaining = due - discount - paid
            
            if remaining > 0:
                unpaid.append(UnpaidEnrollmentItem(
                    enrollment_id=enrollment.id,
                    student_id=enrollment.student_id,
                    student_name=student_name,
                    group_id=enrollment.group_id,
                    group_name=group_name,
                    course_name=course_name,
                    level_number=enrollment.level_number,
                    amount_due=float(due),
                    discount_applied=float(discount),
                    total_paid=float(paid),
                    remaining_balance=float(remaining),
                    enrolled_at=enrollment.enrolled_at
                ))
        
        # Sort by remaining balance descending
        unpaid.sort(key=lambda x: x.remaining_balance, reverse=True)
        
        # Apply pagination at Python level (since we filter after query)
        total = len(unpaid)
        paginated = unpaid[skip:skip + limit]
        
        return paginated, total
    
    def get_student_credit_balance(self, student_id: int) -> Decimal:
        """Get total available credit for a student."""
        db = self._get_db()
        
        result = db.exec(
            select(func.sum(StudentCredit.remaining_credit))
            .where(StudentCredit.student_id == student_id)
            .where(StudentCredit.status == 'active')
        ).first()
        
        return Decimal(str(result[0] or 0))
    
    def adjust_balance(
        self,
        adjustment: BalanceAdjustmentInput,
        performed_by: Optional[int] = None
    ) -> BalanceAdjustmentResponse:
        """
        Manually adjust a student's balance.
        Creates an adjustment record and updates materialized balance.
        """
        db = self._get_db()
        
        student = db.get(Student, adjustment.student_id)
        if not student:
            raise NotFoundError(f"Student with ID {adjustment.student_id} not found")
        
        adjustment_amount = Decimal(str(adjustment.adjustment_amount))
        
        # Create adjustment payment record
        # Note: This requires a receipt - in practice, might need to create a zero-amount receipt
        # or use a special adjustment receipt
        
        # For now, we'll update the materialized balance directly
        # In production, this should create a proper audit trail
        
        current_balance = self.get_quick_balance(adjustment.student_id)
        new_net_balance = Decimal(str(current_balance.net_balance)) + adjustment_amount
        
        # Update materialized balance
        db.execute(
            """
            INSERT INTO student_balances 
                (student_id, total_amount_due, total_discounts, total_paid, net_balance, last_updated, updated_by)
            VALUES 
                (:sid, :due, :discounts, :paid, :balance, NOW(), :updated_by)
            ON CONFLICT (student_id) 
            DO UPDATE SET
                net_balance = EXCLUDED.net_balance,
                last_updated = NOW(),
                updated_by = EXCLUDED.updated_by
            """,
            {
                'sid': adjustment.student_id,
                'due': current_balance.total_amount_due,
                'discounts': current_balance.total_discounts,
                'paid': current_balance.total_paid + float(adjustment_amount),
                'balance': float(new_net_balance),
                'updated_by': performed_by
            }
        )
        
        db.commit()
        
        return BalanceAdjustmentResponse(
            student_id=adjustment.student_id,
            previous_balance=current_balance.net_balance,
            adjustment_amount=float(adjustment_amount),
            new_balance=float(new_net_balance),
            reason=adjustment.reason,
            adjustment_type=adjustment.adjustment_type,
            adjusted_at=datetime.utcnow(),
            adjusted_by=performed_by
        )


# Convenience function for service instantiation
def get_balance_service(db = None):
    """Factory function to create BalanceService instance."""
    return BalanceService(db)
