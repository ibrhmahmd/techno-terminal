"""Notification log queries (read side of the notification module)."""
from datetime import datetime
from typing import Optional

from app.modules.notifications.interfaces.i_notification_repository import (
    NotificationRepositoryInterface,
)


class NotificationLogService:
    def __init__(self, repo: NotificationRepositoryInterface) -> None:
        self._repo = repo

    def get_logs(
        self,
        recipient_type: Optional[str] = None,
        recipient_id: Optional[int] = None,
        status: Optional[str] = None,
        channel: Optional[str] = None,
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        template_id: Optional[int] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list:
        return self._repo.get_logs(
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            status=status,
            channel=channel,
            search=search,
            start_date=start_date,
            end_date=end_date,
            template_id=template_id,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )

    def count_logs(
        self,
        recipient_type: Optional[str] = None,
        recipient_id: Optional[int] = None,
        status: Optional[str] = None,
        channel: Optional[str] = None,
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        template_id: Optional[int] = None,
    ) -> int:
        return self._repo.count_logs(
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            status=status,
            channel=channel,
            search=search,
            start_date=start_date,
            end_date=end_date,
            template_id=template_id,
        )
