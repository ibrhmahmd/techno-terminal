from datetime import date, datetime, timedelta
from typing import Optional
from sqlmodel import Session, select
from sqlalchemy import text
from app.modules.finance.finance_models import Receipt, Payment
from app.shared.datetime_utils import utc_now, date_at_utc_midnight


# ── Receipt ──────────────────────────────────────────────────────────────────


def create_receipt(
    db: Session,
    parent_id: Optional[int],
    method: str,
    received_by: Optional[int],
    paid_at: Optional[datetime] = None,
    notes: Optional[str] = None,
) -> Receipt:
    r = Receipt(
        parent_id=parent_id,
        payment_method=method,
        received_by=received_by,
        paid_at=paid_at or utc_now(),
        notes=notes,
        created_at=utc_now(),
    )
    db.add(r)
    db.flush()
    return r


def set_receipt_number(db: Session, receipt_id: int) -> Receipt:
    r = db.get(Receipt, receipt_id)
    if r:
        year = r.created_at.year if r.created_at else utc_now().year
        r.receipt_number = f"TK-{year}-{receipt_id:05d}"
        db.add(r)
        db.flush()
    return r


def get_receipt(db: Session, receipt_id: int) -> Receipt | None:
    return db.get(Receipt, receipt_id)


def get_receipt_with_lines(db: Session, receipt_id: int) -> dict | None:
    r = db.get(Receipt, receipt_id)
    if not r:
        return None
    lines = list(db.exec(select(Payment).where(Payment.receipt_id == receipt_id)).all())
    return {"receipt": r, "lines": lines}


def get_receipt_total(db: Session, receipt_id: int) -> float:
    stmt = text("""
        SELECT
            COALESCE(SUM(amount) FILTER (WHERE transaction_type IN ('payment','charge')), 0)
            - COALESCE(SUM(amount) FILTER (WHERE transaction_type = 'refund'), 0)
        FROM payments
        WHERE receipt_id = :rid
    """)
    result = db.execute(stmt, {"rid": receipt_id}).scalar()
    return float(result or 0.0)


def list_receipts_by_date(db: Session, target_date: date) -> list[dict]:
    stmt = text("""
        SELECT
            r.id,
            r.receipt_number,
            g.full_name AS parent_name,
            r.payment_method,
            r.paid_at,
            COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
            - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0) AS total
        FROM receipts r
        LEFT JOIN parents g ON r.parent_id = g.id
        LEFT JOIN payments p ON p.receipt_id = r.id
        WHERE DATE(r.paid_at) = :target_date
        GROUP BY r.id, g.full_name
        ORDER BY r.paid_at DESC
    """)
    rows = db.execute(stmt, {"target_date": str(target_date)}).all()
    return [dict(row._mapping) for row in rows]


def search_receipts(
    db: Session,
    from_date: date,
    to_date: date,
    *,
    parent_id: Optional[int] = None,
    student_id: Optional[int] = None,
    receipt_number_contains: Optional[str] = None,
    limit: int = 200,
) -> list[dict]:
    """
    Receipts with line totals in [from_date, to_date] (inclusive, by paid_at in UTC).
    Optional filters: parent, student (any line on receipt), partial receipt_number (ILIKE).
    Uses half-open [start, end) on timestamptz so idx_receipts_paid_at can be used.
    """
    fd_start = date_at_utc_midnight(from_date)
    td_end = date_at_utc_midnight(to_date) + timedelta(days=1)
    where_clauses = ["r.paid_at >= :fd_start AND r.paid_at < :td_end"]
    params: dict = {"fd_start": fd_start, "td_end": td_end, "limit": limit}

    if parent_id is not None:
        where_clauses.append("r.parent_id = :gid")
        params["gid"] = parent_id
    if student_id is not None:
        where_clauses.append(
            "EXISTS (SELECT 1 FROM payments pstu WHERE pstu.receipt_id = r.id AND pstu.student_id = :sid)"
        )
        params["sid"] = student_id
    pat = (receipt_number_contains or "").strip()
    if pat:
        where_clauses.append("r.receipt_number ILIKE :rpat")
        params["rpat"] = f"%{pat}%"

    where_sql = " AND ".join(where_clauses)
    stmt = text(f"""
        SELECT
            r.id,
            r.receipt_number,
            g.full_name AS parent_name,
            r.payment_method,
            r.paid_at,
            COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
            - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0) AS total
        FROM receipts r
        LEFT JOIN parents g ON r.parent_id = g.id
        LEFT JOIN payments p ON p.receipt_id = r.id
        WHERE {where_sql}
        GROUP BY r.id, r.receipt_number, g.full_name, r.payment_method, r.paid_at
        ORDER BY r.paid_at DESC
        LIMIT :limit
    """)
    rows = db.execute(stmt, params).all()
    return [dict(row._mapping) for row in rows]


# ── Payment Lines ─────────────────────────────────────────────────────────────


def add_payment_line(
    db: Session,
    receipt_id: int,
    student_id: int,
    enrollment_id: Optional[int],
    amount: float,
    transaction_type: str,
    payment_type: Optional[str] = None,
    discount: float = 0.0,
    notes: Optional[str] = None,
) -> Payment:
    p = Payment(
        receipt_id=receipt_id,
        student_id=student_id,
        enrollment_id=enrollment_id,
        amount=amount,
        transaction_type=transaction_type,
        payment_type=payment_type,
        discount_amount=discount,
        notes=notes,
        created_at=utc_now(),
    )
    db.add(p)
    db.flush()
    return p


# ── Balance Queries ───────────────────────────────────────────────────────────


def get_enrollment_balance(db: Session, enrollment_id: int) -> dict | None:
    stmt = text("""
        SELECT * FROM v_enrollment_balance WHERE enrollment_id = :eid
    """)
    row = db.execute(stmt, {"eid": enrollment_id}).first()
    return dict(row._mapping) if row else None


def get_student_balances(db: Session, student_id: int) -> list[dict]:
    stmt = text("""
        SELECT vb.*, g.name AS group_name
        FROM v_enrollment_balance vb
        JOIN groups g ON vb.group_id = g.id
        WHERE vb.student_id = :sid
        ORDER BY vb.enrollment_id DESC
    """)
    rows = db.execute(stmt, {"sid": student_id}).all()
    return [dict(row._mapping) for row in rows]


def list_unpaid_enrollments(db: Session, group_id: int) -> list[dict]:
    stmt = text("""
        SELECT vb.enrollment_id, vb.student_id, s.full_name AS student_name, vb.balance
        FROM v_enrollment_balance vb
        JOIN students s ON vb.student_id = s.id
        WHERE vb.group_id = :gid AND vb.balance < 0
        ORDER BY s.full_name
    """)
    rows = db.execute(stmt, {"gid": group_id}).all()
    return [dict(row._mapping) for row in rows]


def get_daily_collections(db: Session, target_date: date) -> list[dict]:
    stmt = text("""
        SELECT
            r.payment_method,
            COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0) AS collected,
            COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0) AS refunded
        FROM receipts r
        JOIN payments p ON p.receipt_id = r.id
        WHERE DATE(r.paid_at) = :target_date
        GROUP BY r.payment_method
    """)
    rows = db.execute(stmt, {"target_date": str(target_date)}).all()
    return [dict(row._mapping) for row in rows]


# ── RepositoryProtocol aliases ────────────────────────────────────────────────
# Primary entity: Receipt
get_by_id = get_receipt
create = create_receipt
list_all = list_receipts_by_date  # Note: requires target_date arg — use functools.partial at call site if needed
