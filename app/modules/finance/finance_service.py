from datetime import datetime, date
from typing import Optional
from app.db.connection import get_session
from app.modules.finance.finance_models import Receipt, Payment
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.finance import finance_repository as repo
from app.shared.exceptions import ValidationError, NotFoundError, BusinessRuleError
from app.shared.validators import validate_positive_amount
from app.shared.constants import PaymentMethod
from app.modules.finance.finance_schemas import ReceiptLineInput

# ── Receipt Lifecycle ─────────────────────────────────────────────────────────


def create_receipt_with_charge_lines(
    payer_name: Optional[str],
    method: PaymentMethod | str,
    received_by_user_id: Optional[int],
    lines: list[ReceiptLineInput],
    notes: Optional[str] = None,
    allow_credit: bool = True,
) -> dict:
    """
    Single transaction: receipt header, persisted receipt number, and all payment lines.
    Preferred for Financial Desk and any flow that must not leave a header without lines
    or a half-visible receipt number across session boundaries (Sprint 1 / B2).
    """
    if not lines:
        raise BusinessRuleError("Cannot create a receipt with no payment lines.")
    with get_session() as db:
        if not allow_credit:
            overpay = preview_overpayment_risk(lines, db=db)
            if overpay:
                raise BusinessRuleError(
                    "One or more lines would create credit. Confirm overpayment before finalizing."
                )
        r = repo.create_receipt(
            db, payer_name, method, received_by_user_id, notes=notes
        )
        repo.set_receipt_number(db, r.id)
        db.refresh(r)
        if not r.receipt_number:
            raise BusinessRuleError(
                "Receipt number was not persisted. Check receipts.receipt_number column and migrations."
            )
        payment_ids: list[int] = []
        for spec in lines:
            ld = spec.model_dump()
            enrollment_id = ld.get("enrollment_id")
            if enrollment_id:
                enr = db.get(Enrollment, enrollment_id)
                if not enr:
                    raise NotFoundError(f"Enrollment {enrollment_id} not found.")
                if enr.status != "active":
                    raise BusinessRuleError(
                        f"Enrollment {enrollment_id} is '{enr.status}', not active."
                    )
            p = repo.add_payment_line(
                db,
                receipt_id=r.id,
                student_id=ld["student_id"],
                enrollment_id=enrollment_id,
                amount=ld["amount"],
                transaction_type="payment",
                payment_type=ld.get("payment_type") or "course_level",
                discount=ld.get("discount") or 0.0,
                notes=ld.get("notes"),
            )
            payment_ids.append(p.id)

            # Auto-link competition payment to TeamMember within the same atomic session
            if ld.get("payment_type") == "competition" and ld.get("team_member_id"):
                from app.modules.competitions.models.team_models import TeamMember
                tm = db.get(TeamMember, ld["team_member_id"])
                if tm:
                    tm.fee_paid = True
                    tm.payment_id = p.id
                    db.add(tm)

        total = repo.get_receipt_total(db, r.id)
        return {
            "receipt_id": r.id,
            "receipt_number": r.receipt_number,
            "payment_method": r.payment_method,
            "paid_at": r.paid_at,
            "lines": len(lines),
            "total": total,
            "payment_ids": payment_ids,
        }


def preview_overpayment_risk(
    lines: list[ReceiptLineInput],
    *,
    db=None,
) -> list[dict]:
    """
    Returns lines that would create/increase credit under P6.
    P6: balance = total_paid - net_due, so debt is negative.
    """
    own_session = db is None
    if own_session:
        cm = get_session()
        db = cm.__enter__()
    try:
        risk_rows: list[dict] = []
        for spec in lines:
            ld = spec.model_dump()
            enrollment_id = ld.get("enrollment_id")
            if not enrollment_id:
                continue
            bal = repo.get_enrollment_balance(db, enrollment_id)
            current_balance = float((bal or {}).get("balance") or 0.0)
            pay_amount = float(ld["amount"])
            projected_balance = current_balance + pay_amount
            if projected_balance > 0:
                debt_before = max(-current_balance, 0.0)
                risk_rows.append(
                    {
                        "student_id": ld["student_id"],
                        "enrollment_id": enrollment_id,
                        "amount": pay_amount,
                        "debt_before": debt_before,
                        "projected_balance": projected_balance,
                        "excess_credit": max(pay_amount - debt_before, 0.0),
                    }
                )
        return risk_rows
    finally:
        if own_session:
            cm.__exit__(None, None, None)


def open_receipt(
    payer_name: Optional[str],
    method: PaymentMethod | str,
    received_by_user_id: Optional[int],
    notes: Optional[str] = None,
) -> Receipt:
    """Creates receipt header + auto-assigns a receipt number."""
    with get_session() as db:
        r = repo.create_receipt(
            db, payer_name, method, received_by_user_id, notes=notes
        )
        repo.set_receipt_number(db, r.id)
        # Refresh after number update
        db.refresh(r)
        return r


def _open_receipt_in_session(
    db,
    payer_name: Optional[str],
    method: PaymentMethod | str,
    received_by_user_id: Optional[int],
    notes: Optional[str] = None,
) -> Receipt:
    """
    Internal variant — creates a receipt header within an existing session.
    Does NOT commit. Used by issue_refund() so receipt + refund line are atomic.
    """
    r = repo.create_receipt(db, payer_name, method, received_by_user_id, notes=notes)
    repo.set_receipt_number(db, r.id)
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
    method: PaymentMethod | str = "cash",
) -> dict:
    """
    Opens a new receipt and adds a refund line based on an original payment.
    ATOMIC — receipt header + refund line + competition fee unmark all commit
    together, or not at all. If any step fails, no orphaned receipt is left.

    Args:
        method: Payment method for the refund receipt. Defaults to 'cash'.
                Pass explicitly for bank transfers, etc. for accurate audit records.
    """
    validate_positive_amount(amount, field="refund amount")

    # Step 1: short read session — just fetch original payment metadata
    with get_session() as db:
        original = db.get(Payment, payment_id)
        if not original:
            raise NotFoundError(f"Original payment {payment_id} not found.")
        student_id = original.student_id
        enrollment_id = original.enrollment_id
        payment_type = original.payment_type

    # Step 2: atomic write session — receipt + refund line + fee unmark together
    with get_session() as db:
        refund_receipt = _open_receipt_in_session(
            db,
            parent_id=None,
            method=method,
            received_by_user_id=received_by_user_id,
            notes=f"Refund: {reason}",
        )
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

        # Unmark competition fee within the SAME session for atomicity
        # NOTE: competitions repo called directly here (not via service) so that
        # the fee unmark and the refund line share one commit boundary.
        if payment_type == "competition":
            from app.modules.competitions.repositories.competition_repository import get_members_by_payment_id
            members = get_members_by_payment_id(db, payment_id)
            for m in members:
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
    # ← SINGLE COMMIT — receipt + refund line + fee unmark or nothing


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


def search_receipts(
    from_date: date,
    to_date: date,
    *,
    payer_name_contains: Optional[str] = None,
    student_id: Optional[int] = None,
    receipt_number_contains: Optional[str] = None,
    limit: int = 200,
) -> list[dict]:
    """Filtered receipt list for Dashboard / ops search (B9)."""
    if to_date < from_date:
        raise ValidationError("End date must be on or after start date.")
    with get_session() as db:
        return repo.search_receipts(
            db,
            from_date,
            to_date,
            payer_name_contains=payer_name_contains,
            student_id=student_id,
            receipt_number_contains=receipt_number_contains,
            limit=limit,
        )


def get_receipt_detail(receipt_id: int) -> dict | None:
    """Returns a receipt with its payment lines and computed total."""
    with get_session() as db:
        data = repo.get_receipt_with_lines(db, receipt_id)
        if not data:
            return None
        total = repo.get_receipt_total(db, receipt_id)
        return {**data, "total": total}


def get_enrollment_balance(enrollment_id: int) -> dict | None:
    """
    Row from `v_enrollment_balance`. **P6:** `balance` = total_paid − net_due
    (negative = debt, zero = settled, positive = credit).
    """
    with get_session() as db:
        return repo.get_enrollment_balance(db, enrollment_id)


# ── Unpaid Competition Fees ───────────────────────────────────────────────────


def get_unpaid_competition_fees(student_id: int) -> list[dict]:
    """
    Returns a list of unpaid competition fee records for a student.
    Each dict contains all the information the Financial Desk UI needs to
    render a checkbox payment line:
      - team_member_id  : int              (FK to mark fee paid)
      - team_id         : int
      - team_name       : str
      - competition_name: str
      - member_share    : float            (snapshotted amount at registration time)
      - student_id      : int
    """
    from app.modules.competitions.models.team_models import TeamMember, Team
    from app.modules.competitions.models.competition_models import Competition, CompetitionCategory
    from sqlmodel import select

    with get_session() as db:
        stmt = (
            select(TeamMember, Team, CompetitionCategory, Competition)
            .join(Team, TeamMember.team_id == Team.id)
            .join(CompetitionCategory, Team.category_id == CompetitionCategory.id)
            .join(Competition, CompetitionCategory.competition_id == Competition.id)
            .where(
                TeamMember.student_id == student_id,
                TeamMember.fee_paid == False,
                TeamMember.member_share > 0,
            )
        )
        rows = db.exec(stmt).all()
        result = []
        for tm, team, cat, comp in rows:
            result.append({
                "team_member_id": tm.id,
                "team_id": team.id,
                "team_name": team.team_name,
                "competition_name": f"{comp.name}" + (f" – {comp.edition}" if comp.edition else ""),
                "category_name": cat.category_name,
                "member_share": float(tm.member_share),
                "student_id": tm.student_id,
            })
        return result


def generate_receipt_pdf(receipt_id: int) -> bytes:
    """
    Generates a PDF for a receipt, fetching the parent name and line items.
    """
    from app.modules.finance.receipt_pdf import build_receipt_pdf
    from app.modules.crm.models import Parent, Student
    
    with get_session() as db:
        data = repo.get_receipt_with_lines(db, receipt_id)
        if not data:
            raise NotFoundError(f"Receipt {receipt_id} not found.")
        
        receipt = data["receipt"]
        lines = data["lines"]
        total = repo.get_receipt_total(db, receipt_id)
        
        # Try to find a parent name from the lines (assuming one parent per receipt typically)
        parent_name = "N/A"
        if lines:
            first_student_id = lines[0].student_id
            student = db.get(Student, first_student_id)
            if student and student.parent_id:
                parent = db.get(Parent, student.parent_id)
                if parent:
                    parent_name = parent.full_name
        
        # Build the PDF bytes
        pdf_bytes = build_receipt_pdf(
            receipt=receipt,
            lines=lines,
            total=total,
            parent_name=parent_name
        )
        return pdf_bytes
