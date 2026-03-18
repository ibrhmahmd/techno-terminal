from datetime import datetime, date
from typing import Optional
from app.db.connection import get_session
from app.modules.finance.models import Receipt, Payment
from app.modules.enrollments.models import Enrollment
from app.modules.finance import repository as repo
from app.shared.exceptions import ValidationError, NotFoundError, BusinessRuleError
from app.shared.validators import validate_positive_amount


# ── Receipt Lifecycle ─────────────────────────────────────────────────────────


def open_receipt(
    guardian_id: Optional[int],
    method: str,
    received_by_user_id: Optional[int],
    notes: Optional[str] = None,
) -> Receipt:
    """Creates receipt header + auto-assigns a receipt number."""
    with get_session() as db:
        r = repo.create_receipt(
            db, guardian_id, method, received_by_user_id, notes=notes
        )
        repo.set_receipt_number(db, r.id)
        # Refresh after number update
        db.refresh(r)
        return r


def add_charge_line(
    receipt_id: int,
    student_id: int,
    enrollment_id: Optional[int],
    amount: float,
    payment_type: str = "course_level",
    discount: float = 0.0,
    notes: Optional[str] = None,
) -> Payment:
    """Records a payment received for a student's enrollment."""
    validate_positive_amount(amount, field="amount")
    with get_session() as db:
        # Validate enrollment if provided
        if enrollment_id:
            enr = db.get(Enrollment, enrollment_id)
            if not enr:
                raise NotFoundError(f"Enrollment {enrollment_id} not found.")
            if enr.status != "active":
                raise BusinessRuleError(
                    f"Enrollment {enrollment_id} is '{enr.status}', not active."
                )
        return repo.add_payment_line(
            db,
            receipt_id=receipt_id,
            student_id=student_id,
            enrollment_id=enrollment_id,
            amount=amount,
            transaction_type="payment",
            payment_type=payment_type,
            discount=discount,
            notes=notes,
        )


def finalize_receipt(receipt_id: int) -> dict:
    """Validates the receipt has at least 1 payment line and returns a summary."""
    with get_session() as db:
        data = repo.get_receipt_with_lines(db, receipt_id)
        if not data:
            raise NotFoundError(f"Receipt {receipt_id} not found.")
        if not data["lines"]:
            raise BusinessRuleError("Cannot finalize a receipt with no payment lines.")
        total = repo.get_receipt_total(db, receipt_id)
        r = data["receipt"]
        return {
            "receipt_id": r.id,
            "receipt_number": r.receipt_number,
            "payment_method": r.payment_method,
            "paid_at": r.paid_at,
            "lines": len(data["lines"]),
            "total": total,
        }


def issue_refund(
    payment_id: int,
    amount: float,
    reason: str,
    received_by_user_id: Optional[int],
) -> dict:
    """Opens a new receipt and adds a refund line based on an original payment."""
    validate_positive_amount(amount, field="refund amount")
    with get_session() as db:
        original_payment = db.get(Payment, payment_id)
        if not original_payment:
            raise NotFoundError(f"Original payment {payment_id} not found.")

        student_id = original_payment.student_id
        enrollment_id = original_payment.enrollment_id
        payment_type = original_payment.payment_type

    # Create refund receipt
    refund_receipt = open_receipt(
        guardian_id=None,
        method="cash",  # default; UI can override
        received_by_user_id=received_by_user_id,
        notes=f"Refund: {reason}",
    )

    with get_session() as db:
        repo.add_payment_line(
            db,
            receipt_id=refund_receipt.id,
            student_id=student_id,
            enrollment_id=enrollment_id,
            amount=amount,
            transaction_type="refund",
            payment_type=payment_type,
            notes=reason,
        )

        # Unmark competition fee if applicable
        if payment_type == "competition":
            from app.modules.competitions.models import TeamMember
            from sqlmodel import select

            stmt = select(TeamMember).where(TeamMember.payment_id == payment_id)
            for m in db.exec(stmt).all():
                m.fee_paid = False
                m.payment_id = None
                db.add(m)

        balance_data = None
        if enrollment_id:
            balance_data = repo.get_enrollment_balance(db, enrollment_id)

        return {
            "receipt_number": refund_receipt.receipt_number,
            "refunded_amount": amount,
            "new_balance": balance_data["balance"] if balance_data else None,
        }


# ── Balance & Reporting ───────────────────────────────────────────────────────


def get_student_financial_summary(student_id: int) -> list[dict]:
    """Returns all enrollment balances for a student."""
    with get_session() as db:
        return repo.get_student_balances(db, student_id)


def get_daily_collections(target_date: Optional[date] = None) -> list[dict]:
    """Sum of payments per payment method for a given date (defaults to today)."""
    if target_date is None:
        target_date = date.today()
    with get_session() as db:
        return repo.get_daily_collections(db, target_date)


def get_daily_receipts(target_date: Optional[date] = None) -> list[dict]:
    """All receipts issued on a given date with totals."""
    if target_date is None:
        target_date = date.today()
    with get_session() as db:
        return repo.list_receipts_by_date(db, target_date)


def get_receipt_detail(receipt_id: int) -> dict | None:
    """Returns a receipt with its payment lines and computed total."""
    with get_session() as db:
        data = repo.get_receipt_with_lines(db, receipt_id)
        if not data:
            return None
        total = repo.get_receipt_total(db, receipt_id)
        return {**data, "total": total}


def get_enrollment_balance(enrollment_id: int) -> dict | None:
    with get_session() as db:
        return repo.get_enrollment_balance(db, enrollment_id)
