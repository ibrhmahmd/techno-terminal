"""
app/modules/finance/repositories/receipt_repository.py
─────────────────────────────────────────────────────
Concrete implementation of receipt repository.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import text
from sqlmodel import Session

from app.modules.finance import Receipt
from app.modules.finance.interfaces import (
    IReceiptRepository,
    ReceiptWithLinesDTO,
    CreateReceiptDTO,
    SearchReceiptsDTO,
)
from app.modules.finance import DailyReceiptItem, ReceiptSearchItem
from app.shared.datetime_utils import date_at_utc_midnight, utc_now


class ReceiptRepository(IReceiptRepository):
    """Repository for receipt data access operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, dto: CreateReceiptDTO) -> Receipt:
        """Create a new receipt record."""
        receipt = Receipt(
            payer_name=dto.payer_name,
            payment_method=dto.payment_method,
            received_by_user_id=dto.received_by_user_id,
            notes=dto.notes,
            paid_at=utc_now(),
        )
        self._session.add(receipt)
        self._session.flush()
        return receipt

    def set_receipt_number(self, receipt_id: int) -> None:
        """Assign a formatted receipt number to an existing receipt."""
        stmt = text(
            """
            UPDATE receipts
            SET receipt_number = 'R-' || TO_CHAR(NOW() AT TIME ZONE 'UTC', 'YYYYMMDD') || '-' || id
            WHERE id = :rid
            """
        )
        self._session.execute(stmt, {"rid": receipt_id})

    def get_by_id(self, receipt_id: int) -> Optional[Receipt]:
        """Get receipt by ID."""
        return self._session.get(Receipt, receipt_id)

    def get_with_lines(self, receipt_id: int) -> Optional[ReceiptWithLinesDTO]:
        """Get receipt with its payment lines."""
        from app.modules.finance import Payment

        receipt = self.get_by_id(receipt_id)
        if not receipt:
            return None

        payments = (
            self._session.query(Payment)
            .where(Payment.receipt_id == receipt_id)
            .all()
        )

        return ReceiptWithLinesDTO(receipt=receipt, lines=list(payments))

    def get_total(self, receipt_id: int) -> Decimal:
        """Calculate total amount for a receipt (payments - refunds)."""
        stmt = text(
            """
            SELECT COALESCE(
                SUM(CASE 
                    WHEN transaction_type IN ('payment', 'charge') THEN amount 
                    ELSE 0 
                END),
                0
            ) - COALESCE(
                SUM(CASE 
                    WHEN transaction_type = 'refund' THEN amount 
                    ELSE 0 
                END),
                0
            ) as total
            FROM payments
            WHERE receipt_id = :rid
            """
        )
        result = self._session.execute(stmt, {"rid": receipt_id}).scalar()
        return Decimal(str(result or 0))

    def list_by_date(
        self, target_date: date, limit: int = 1000
    ) -> List[DailyReceiptItem]:
        """List receipts issued on a specific date."""
        fd_start = date_at_utc_midnight(target_date)
        td_end = fd_start + timedelta(days=1)

        stmt = text(
            """
            SELECT 
                r.id as receipt_id,
                r.receipt_number,
                r.payer_name,
                COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
                - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0) AS total,
                r.payment_method,
                r.paid_at as issued_at
            FROM receipts r
            LEFT JOIN payments p ON p.receipt_id = r.id
            WHERE r.paid_at >= :fd_start AND r.paid_at < :td_end
            GROUP BY r.id, r.receipt_number, r.payer_name, r.payment_method, r.paid_at
            ORDER BY r.paid_at DESC
            LIMIT :limit
            """
        )
        rows = self._session.execute(
            stmt, {"fd_start": fd_start, "td_end": td_end, "limit": limit}
        ).all()

        return [
            DailyReceiptItem(
                receipt_id=row.receipt_id,
                receipt_number=row.receipt_number,
                payer_name=row.payer_name,
                total_amount=float(row.total or 0),
                payment_method=row.payment_method or "unknown",
                issued_at=row.issued_at,
            )
            for row in rows
        ]

    def search(self, criteria: SearchReceiptsDTO) -> List[ReceiptSearchItem]:
        """Search receipts with filters."""
        fd_start = date_at_utc_midnight(criteria.from_date)
        td_end = date_at_utc_midnight(criteria.to_date) + timedelta(days=1)
        where_clauses = ["r.paid_at >= :fd_start AND r.paid_at < :td_end"]
        params: dict = {"fd_start": fd_start, "td_end": td_end, "limit": criteria.limit}

        if criteria.payer_name_contains:
            where_clauses.append("r.payer_name ILIKE :pnam")
            params["pnam"] = f"%{criteria.payer_name_contains.strip()}%"

        if criteria.student_id is not None:
            where_clauses.append(
                "EXISTS (SELECT 1 FROM payments pstu WHERE pstu.receipt_id = r.id AND pstu.student_id = :sid)"
            )
            params["sid"] = criteria.student_id

        pat = (criteria.receipt_number_contains or "").strip()
        if pat:
            where_clauses.append("r.receipt_number ILIKE :rpat")
            params["rpat"] = f"%{pat}%"

        where_sql = " AND ".join(where_clauses)
        stmt = text(f"""
            SELECT
                r.id,
                r.receipt_number,
                r.payer_name,
                r.payment_method,
                r.paid_at
            FROM receipts r
            WHERE {where_sql}
            ORDER BY r.paid_at DESC
            LIMIT :limit
        """)
        rows = self._session.execute(stmt, params).all()

        return [
            ReceiptSearchItem(
                id=row.id,
                receipt_number=row.receipt_number,
                payer_name=row.payer_name,
                payment_method=row.payment_method or "unknown",
                paid_at=row.paid_at,
            )
            for row in rows
        ]
