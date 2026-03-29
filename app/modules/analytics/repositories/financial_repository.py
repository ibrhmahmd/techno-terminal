"""
app/modules/analytics/repositories/financial_repository.py
──────────────────────────────────────────────────────────
Data access layer for financial analytics.
"""

from datetime import date
from sqlmodel import Session
from sqlalchemy import text
from app.modules.analytics.schemas import (
    RevenueByDateDTO,
    RevenueByMethodDTO,
    OutstandingByGroupDTO,
    TopDebtorDTO,
)


def get_revenue_by_date(db: Session, start: date, end: date) -> list[RevenueByDateDTO]:
    """Daily revenue totals between two dates."""
    stmt = text("""
        SELECT
            DATE(r.paid_at) AS day,
            COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
              - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0) AS net_revenue
        FROM receipts r
        JOIN payments p ON p.receipt_id = r.id
        WHERE DATE(r.paid_at) BETWEEN :start AND :end
        GROUP BY day
        ORDER BY day
    """)
    rows = db.execute(stmt, {"start": str(start), "end": str(end)}).all()
    return [RevenueByDateDTO(**r._mapping) for r in rows]


def get_revenue_by_method(db: Session, start: date, end: date) -> list[RevenueByMethodDTO]:
    """Revenue totals grouped by payment method between two dates."""
    stmt = text("""
        SELECT
            r.payment_method,
            COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
              - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0) AS net_revenue,
            COUNT(DISTINCT r.id) AS receipt_count
        FROM receipts r
        JOIN payments p ON p.receipt_id = r.id
        WHERE DATE(r.paid_at) BETWEEN :start AND :end
        GROUP BY r.payment_method
        ORDER BY net_revenue DESC
    """)
    rows = db.execute(stmt, {"start": str(start), "end": str(end)}).all()
    return [RevenueByMethodDTO(**r._mapping) for r in rows]


def get_outstanding_by_group(db: Session) -> list[OutstandingByGroupDTO]:
    """Sum of debt (EGP) per active group — P6: balance < 0 means owes."""
    stmt = text("""
        SELECT
            g.id AS group_id,
            g.name AS group_name,
            c.name AS course_name,
            COUNT(DISTINCT vb.student_id) AS students_with_balance,
            SUM(CASE WHEN vb.balance < 0 THEN -vb.balance ELSE 0 END) AS total_outstanding
        FROM v_enrollment_balance vb
        JOIN groups g ON vb.group_id = g.id
        JOIN courses c ON g.course_id = c.id
        WHERE vb.balance < 0 AND g.status = 'active'
        GROUP BY g.id, g.name, c.name
        ORDER BY total_outstanding DESC
    """)
    rows = db.execute(stmt).all()
    return [OutstandingByGroupDTO(**r._mapping) for r in rows]


def get_top_debtors(db: Session, limit: int = 15) -> list[TopDebtorDTO]:
    """Students with the highest combined debt (P6: positive EGP owed)."""
    stmt = text("""
        SELECT
            st.id AS student_id,
            st.full_name AS student_name,
            g.full_name AS parent_name,
            g.phone_primary,
            SUM(CASE WHEN vb.balance < 0 THEN -vb.balance ELSE 0 END) AS total_outstanding
        FROM v_enrollment_balance vb
        JOIN students st ON vb.student_id = st.id
        LEFT JOIN student_parents sg ON sg.student_id = st.id AND sg.is_primary = TRUE
        LEFT JOIN parents g ON g.id = sg.parent_id
        WHERE vb.balance < 0
        GROUP BY st.id, st.full_name, g.full_name, g.phone_primary
        ORDER BY total_outstanding DESC
        LIMIT :limit
    """)
    rows = db.execute(stmt, {"limit": limit}).all()
    return [TopDebtorDTO(**r._mapping) for r in rows]
