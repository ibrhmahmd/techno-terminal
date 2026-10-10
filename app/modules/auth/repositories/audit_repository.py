from datetime import datetime
from typing import Optional

from sqlmodel import Session, select, func

from app.modules.auth.models.audit_log import AuditLog
from app.modules.auth.schemas.auth_schemas import AuditLogEntryDTO, AuditLogQueryResult


class AuditRepository:
    """Repository for audit log data access."""

    def __init__(self, session: Session):
        self._session = session

    def create_log(self, log: AuditLog) -> AuditLog:
        self._session.add(log)
        self._session.flush()
        return log

    def list_logs(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> AuditLogQueryResult:
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

        total = self._session.exec(count_query).one()
        results = list(self._session.exec(query).all())
        dtos = [
            AuditLogEntryDTO.model_validate(log, from_attributes=True)
            for log in results
        ]
        return AuditLogQueryResult(items=dtos, total=total)

    def get_last_login_event(self, user_id: int) -> AuditLog | None:
        stmt = (
            select(AuditLog)
            .where(
                AuditLog.user_id == user_id,
                AuditLog.event_type == "login_success",
            )
            .order_by(AuditLog.created_at.desc())
            .limit(1)
        )
        return self._session.exec(stmt).first()