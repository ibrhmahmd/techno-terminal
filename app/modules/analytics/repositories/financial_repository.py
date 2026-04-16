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
    RevenueMetricsDTO,
    RevenueForecastDTO
)
from dateutil.relativedelta import relativedelta


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


def get_revenue_metrics(db: Session, months: int = 6) -> RevenueMetricsDTO:
    """Extended revenue metrics with trend analysis for the last N months."""
    period_end = date.today()
    period_start = period_end - relativedelta(months=months)
    previous_period_start = period_start - relativedelta(months=months)
    
    # 1. Fetch ALL daily revenue across previous + current periods in ONE query
    daily_revenue_stmt = text("""
        SELECT
            DATE(r.paid_at) AS day,
            COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment','charge')), 0)
              - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0) AS net_revenue
        FROM receipts r
        JOIN payments p ON p.receipt_id = r.id
        WHERE DATE(r.paid_at) BETWEEN :prev_start AND :end
        GROUP BY day
        ORDER BY day
    """)
    daily_rows = db.execute(
        daily_revenue_stmt, 
        {"prev_start": str(previous_period_start), "end": str(period_end)}
    ).all()
    
    # Separate into current vs previous periods in python
    monthly_breakdown = []
    total_revenue = 0.0
    previous_period_revenue = 0.0
    
    for row in daily_rows:
        day_val = row.day
        if isinstance(day_val, str):
            from datetime import datetime
            day_val = datetime.strptime(day_val, "%Y-%m-%d").date()
        
        if day_val >= period_start:
            monthly_breakdown.append(RevenueByDateDTO(day=day_val, net_revenue=row.net_revenue))
            total_revenue += float(row.net_revenue)
        else:
            previous_period_revenue += float(row.net_revenue)

    # 2. Get total receipts for current period
    total_receipts_stmt = text("""
        SELECT COUNT(DISTINCT r.id) 
        FROM receipts r
        WHERE DATE(r.paid_at) BETWEEN :start AND :end
    """)
    total_receipts = db.execute(
        total_receipts_stmt, 
        {"start": str(period_start), "end": str(period_end)}
    ).scalar() or 0
    
    # Calculate trend
    if previous_period_revenue > 0:
        revenue_change_pct = round(
            ((total_revenue - previous_period_revenue) / previous_period_revenue) * 100, 2
        )
    else:
        revenue_change_pct = 100.0 if total_revenue > 0 else 0.0
    
    if revenue_change_pct > 5:
        trend_direction = "up"
    elif revenue_change_pct < -5:
        trend_direction = "down"
    else:
        trend_direction = "stable"
    
    avg_revenue_per_receipt = (
        round(total_revenue / total_receipts, 2) if total_receipts > 0 else 0.0
    )
    
    return RevenueMetricsDTO(
        period_start=period_start,
        period_end=period_end,
        total_revenue=round(total_revenue, 2),
        total_receipts=total_receipts,
        avg_revenue_per_receipt=avg_revenue_per_receipt,
        previous_period_revenue=round(previous_period_revenue, 2),
        revenue_change_pct=revenue_change_pct,
        trend_direction=trend_direction,
        monthly_breakdown=monthly_breakdown,
    )


def get_revenue_forecast(db: Session, months_ahead: int = 3) -> list[RevenueForecastDTO]:
    """Generate revenue forecast for future months based on historical trends."""
    
    # Get historical data for trend calculation (last 6 months)
    end_date = date.today()
    start_date = end_date - relativedelta(months=6)
    
    historical = get_revenue_by_date(db, start_date, end_date)
    
    # Calculate average monthly revenue and growth trend
    if historical:
        avg_revenue = sum(day.net_revenue for day in historical) / len(historical)
        
        # Simple trend: compare first half vs second half
        mid = len(historical) // 2
        first_half_avg = sum(day.net_revenue for day in historical[:mid]) / mid if mid > 0 else avg_revenue
        second_half_avg = sum(day.net_revenue for day in historical[mid:]) / (len(historical) - mid) if len(historical) > mid else avg_revenue
        
        monthly_growth_rate = (second_half_avg - first_half_avg) / first_half_avg if first_half_avg > 0 else 0
    else:
        avg_revenue = 0
        monthly_growth_rate = 0
    
    # Generate forecast
    forecast = []
    for i in range(1, months_ahead + 1):
        forecast_month = end_date + relativedelta(months=i)
        month_str = forecast_month.strftime("%Y-%m")
        
        # Apply growth trend
        predicted = avg_revenue * (1 + monthly_growth_rate) ** i
        
        # Confidence interval (±20%)
        confidence_lower = predicted * 0.8
        confidence_upper = predicted * 1.2
        
        forecast.append(RevenueForecastDTO(
            month=month_str,
            predicted_revenue=round(predicted, 2),
            confidence_lower=round(confidence_lower, 2),
            confidence_upper=round(confidence_upper, 2)
        ))
    
    return forecast
