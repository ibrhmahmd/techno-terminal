from datetime import datetime
from typing import Optional

from app.db.connection import get_session
import app.modules.auth.repositories.audit_repository as audit_repo
from app.modules.auth.models.audit_log import AuditLog, AuditLogEventType
from app.modules.auth.schemas.auth_schemas import AuditLogEntryDTO, AuditLogQueryResult


class AuditService:
    def log_event(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> AuditLog:
        with get_session() as session:
            log = AuditLog(
                user_id=user_id,
                event_type=event_type,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details,
            )
            result = audit_repo.create_log(session, log)
            session.commit()
            session.refresh(result)
            return result

    def query_logs(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> AuditLogQueryResult:
        with get_session() as session:
            logs, total = audit_repo.list_logs(
                session,
                event_type=event_type,
                user_id=user_id,
                from_date=from_date,
                to_date=to_date,
                skip=skip,
                limit=limit,
            )
            dtos = [
                AuditLogEntryDTO.model_validate(log, from_attributes=True)
                for log in logs
            ]
            return AuditLogQueryResult(items=dtos, total=total)

    def query_logins(
        self,
        user_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> AuditLogQueryResult:
        return self.query_logs(
            event_type=AuditLogEventType.LOGIN_SUCCESS,
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
            skip=skip,
            limit=limit,
        )

    def query_password_changes(
        self,
        user_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> AuditLogQueryResult:
        return self.query_logs(
            event_type=AuditLogEventType.PASSWORD_CHANGE,
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
            skip=skip,
            limit=limit,
        )

    def query_failed_attempts(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> AuditLogQueryResult:
        return self.query_logs(
            event_type=AuditLogEventType.LOGIN_FAILURE,
            from_date=from_date,
            to_date=to_date,
            skip=skip,
            limit=limit,
        )
