import logging
from datetime import datetime
from typing import Optional

from app.db.uow import UnitOfWork
import app.modules.auth.repositories.audit_repository as audit_repo
from app.modules.auth.models.audit_log import AuditLog, AuditLogEventType
from app.modules.auth.schemas.auth_schemas import AuditLogEntryDTO, AuditLogQueryResult

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self._repo = audit_repo.AuditRepository(uow.session)

    def log_event(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> Optional[AuditLog]:
        """Persist an audit event without ever breaking the calling request.

        Audit writes must be best-effort: an infrastructure hiccup (e.g. a
        transient RLS/pooler error) degrades to a warning instead of a
        traceback in an auth response path.

        Uses a SAVEPOINT so failures don't poison the outer transaction.
        """
        try:
            with self._uow.session.begin_nested():
                log = AuditLog(
                    user_id=user_id,
                    event_type=event_type,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details=details,
                )
                result = self._repo.create_log(log)
                # Flush to get the ID, but don't commit - caller commits
                self._uow.session.flush()
                self._uow.session.refresh(result)
                return result
        except Exception:
            logger.warning(
                "audit_log write failed (event_type=%s, user_id=%s) - "
                "continuing without this audit trail",
                event_type,
                user_id,
                exc_info=True,
            )
            return None

    def query_logs(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> AuditLogQueryResult:
        return self._repo.list_logs(
            event_type=event_type,
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
            skip=skip,
            limit=limit,
        )

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

    def get_last_login_event(self, user_id: int) -> AuditLog | None:
        return self._repo.get_last_login_event(user_id)