from datetime import datetime
from typing import Optional

from sqlmodel import Session, select, func

from app.modules.auth.models.audit_log import AuditLog


def create_log(session: Session, log: AuditLog) -> AuditLog:
    session.add(log)
    session.flush()
    return log


def list_logs(
    session: Session,
    event_type: Optional[str] = None,
    user_id: Optional[int] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[AuditLog], int]:
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    if event_type:
        query = query.where(AuditLog.event_type == event_type)
        count_query = count_query.where(AuditLog.event_type == event_type)
    if user_id is not None:
        query = query.where(AuditLog.user_id == user_id)
        count_query = count_query.where(AuditLog.user_id == user_id)
    if from_date:
        query = query.where(AuditLog.created_at >= from_date)
        count_query = count_query.where(AuditLog.created_at >= from_date)
    if to_date:
        query = query.where(AuditLog.created_at <= to_date)
        count_query = count_query.where(AuditLog.created_at <= to_date)

    query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)

    total = session.exec(count_query).one()
    results = list(session.exec(query).all())
    return results, total
