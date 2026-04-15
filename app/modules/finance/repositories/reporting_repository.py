"""
app/modules/finance/repositories/reporting_repository.py
────────────────────────────────────────────────────────
Reporting repository implementation.
"""
from datetime import date, timedelta
from typing import List

from sqlalchemy import text
from sqlmodel import Session

from app.modules.finance import DailyCollectionItem, UnpaidCompFeeItem
from app.modules.finance.interfaces import IReportingRepository
from app.shared.datetime_utils import date_at_utc_midnight


class ReportingRepository(IReportingRepository):
    """Repository for reporting and analytics data access."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_daily_collections(
        self, target_date: date
    ) -> List[DailyCollectionItem]:
        """Get daily collections grouped by payment method."""
        fd_start = date_at_utc_midnight(target_date)
        fd_end = fd_start + timedelta(days=1)

        stmt = text(
            """
            SELECT
                payment_method,
                SUM(amount) as total_amount,
                COUNT(DISTINCT receipt_id) as receipt_count
            FROM payments p
            JOIN receipts r ON p.receipt_id = r.id
            WHERE p.transaction_type = 'payment'
            AND r.paid_at >= :fd_start AND r.paid_at < :fd_end
            GROUP BY payment_method
            """
        )
        results = self._session.exec(
            stmt, {"fd_start": fd_start, "fd_end": fd_end}
        ).all()

        return [
            DailyCollectionItem(
                payment_method=row.payment_method or "unknown",
                total_amount=float(row.total_amount or 0),
                receipt_count=row.receipt_count or 0,
                target_date=target_date,
            )
            for row in results
        ]

    def get_unpaid_competition_fees(
        self, student_id: int
    ) -> List[UnpaidCompFeeItem]:
        """Get unpaid competition fees for a student."""
        stmt = text(
            """
            SELECT
                tm.id as team_member_id,
                t.id as team_id,
                t.team_name,
                c.name as competition_name,
                cat.name as category_name,
                COALESCE(tm.fee_share, 0) as member_share,
                s.id as student_id
            FROM team_members tm
            JOIN teams t ON tm.team_id = t.id
            JOIN competitions c ON t.competition_id = c.id
            JOIN categories cat ON t.category_id = cat.id
            JOIN students s ON tm.student_id = s.id
            LEFT JOIN payments p ON p.student_id = s.id
                AND p.payment_type = 'competition'
                AND p.transaction_type = 'payment'
                AND p.payment_metadata->>'team_member_id' = tm.id::text
            WHERE tm.student_id = :student_id
            AND p.id IS NULL
            AND COALESCE(tm.fee_share, 0) > 0
            """
        )
        results = self._session.exec(stmt, {"student_id": student_id}).all()

        return [
            UnpaidCompFeeItem(
                team_member_id=row.team_member_id,
                team_id=row.team_id,
                team_name=row.team_name,
                competition_name=row.competition_name,
                category_name=row.category_name,
                member_share=float(row.member_share),
                student_id=row.student_id,
            )
            for row in results
        ]
